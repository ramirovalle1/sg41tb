import io
import os
import sys
import json
import random
import subprocess
import xlrd
from decorators import secure_module
from sga.commonviews import addUserData
from datetime import datetime, time, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import render, redirect
from django.template.context import RequestContext
from django.db.models.query_utils import Q
from django.template.loader import get_template
from django.utils.encoding import force_str



@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
def view(request):
    hoy = datetime.now().date()

    if request.method == 'POST':
        if 'action' in request.POST:
            action = request.POST['action']

            if action == 'firmarActa':
                return ViewSolicitudes.render_firmar(request)
            elif action == 'cancelarSolicitud':
                return ViewSolicitudes.render_cancelar_solicitud(request)

        return JsonResponse({"isSuccess": False, "message": f"Acción no encontrada"})
    else:
        if 'action' in request.GET:
            action = request.GET['action']

            if action == 'loadFormFirma':
                return ViewSolicitudes.render_load_form_firma(request)
        else:
            return ViewSolicitudes.render_load_init(request)


class ViewSolicitudes:

    @staticmethod
    def render_load_init(request: HttpRequest) -> HttpResponse:
        from firmaec.models import Solicitud
        from core.my_pager import MyPaginator
        try:
            data = {}
            addUserData(request, data)
            ePersona = data['persona']
            data['title'] = 'Solicitudes de firmas'
            data['ePersona'] = ePersona
            filtros, s, ide, idt, url_vars = Q(es_activo=True), request.GET.get('s', ''), request.GET.get('ide', '-1'), request.GET.get('idt', '-1'), ''
            if not ePersona.usuario.is_superuser:
                filtros &= Q(responsable=ePersona)
            if s:
                if s.isdigit():
                    filtros &= (Q(id=s))
                else:
                    filtros &= (Q(descripcion__icontains=s))
                data['s'] = f"{s}"
                url_vars += f"&s={s}"
            try:
                ide = int(ide)
            except ValueError:
                ide = -1
            try:
                idt = int(idt)
            except ValueError:
                idt = -1
            if ide > -1:
                filtros &= Q(estado=ide)
            if idt > -1:
                filtros &= Q(tipo=idt)
            url_vars += f"&ide={ide}&idt={idt}"
            eSolicitudes = Solicitud.objects.filter(filtros).order_by('fecha_creacion', 'estado')
            paging = MyPaginator(eSolicitudes, 15)
            p = 1
            try:
                sessionPage = 1
                if 'pager' in request.session:
                    sessionPage = int(request.session['pager'])
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                else:
                    p = sessionPage
                try:
                    page = paging.page(p)
                except:
                    p = 1
                page = paging.page(p)
            except:
                page = paging.page(p)
            request.session['pager'] = p
            data['paging'] = paging
            data['page'] = page
            data['paged_ranges'] = paging.paginated_ranges(p)
            data['eSolicitudes'] = page.object_list
            data['url_vars'] = url_vars
            data['eEstados'] = Solicitud.Estados.choices
            data['eTipos'] = Solicitud.Tipos.choices
            data['ide'] = ide
            data['idt'] = idt
            return render(request, "firma_ec/solicitudes/view.html", data)
        except Exception as ex:
            return redirect(f"/?info={ex.__str__()}")

    @staticmethod
    def render_load_form_firma(request: HttpRequest) -> JsonResponse:
        from firmaec.forms import FirmaECForm
        from firmaec.models import Solicitud
        with transaction.atomic():
            try:
                id = request.GET.get('id', 0)
                try:
                    eSolicitud = Solicitud.objects.get(id=id)
                except ObjectDoesNotExist:
                    raise NameError(u"Solicitud no encontrada")
                data = {}
                addUserData(request, data)
                ePersona = data['persona']
                f = FirmaECForm()
                data['form'] = f
                data['canViewVisor'] = False
                data['id'] = id
                data['action'] = 'firmarActa'
                if eSolicitud.tipo == Solicitud.Tipos.ACTA_CALIFICACION:
                    eMateria = eSolicitud.content_object
                    eRepositorioActaCalificacion = eMateria.mi_repositorio_acta_calificacion()
                    puede_firmar = eRepositorioActaCalificacion.puede_firmar(ePersona.id)
                    if not puede_firmar:
                        raise NameError(u"No puede firmar acta de calificaciones")
                template = get_template("firma_ec/forms/default.html")
                return JsonResponse({"isSuccess": True, "message": f"Se construyo formulario correctamente", 'html': template.render(data)})
            except Exception as ex:
                transaction.set_rollback(True)
                print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
                return JsonResponse({"isSuccess": False, "message": f"Error al obtener los datos. {ex.__str__()}"})

    @staticmethod
    def render_firmar(request: HttpRequest) -> JsonResponse:
        from firmaec.models import RepositorioActaCalificacion, Solicitud, SolicitudFirmada
        from documental.models import Repositorio
        from firmaec.forms import FirmaECForm
        from django.core.files import File as DjangoFile
        from sga.funciones import remover_caracteres_especiales_unicode
        from core.my_firma import MY_JavaFirmaEc
        from firmaec.functions import elimina_tildes

        def obtener_solicitud(id: int):
            try:
                return Solicitud.objects.get(id=id)
            except Solicitud.DoesNotExist:
                raise NameError("Solicitud no encontrada")

        def verificar_archivo_solicitud(eSolicitud):
            if not eSolicitud.archivo:
                raise NameError("No se encuentra archivo a firmar")

        def firmar_acta_calificaciones(ePersona, eSolicitud, f):
            eMateria = eSolicitud.content_object
            eRepositorioActaCalificacion = eMateria.mi_repositorio_acta_calificacion()

            if not eRepositorioActaCalificacion.puede_firmar(ePersona.id):
                raise NameError("No puede firmar acta de calificaciones")

            eFirmaActaCalificacion = eRepositorioActaCalificacion.secuencia_firma().filter(responsable=ePersona).first()

            palabras = f'{eFirmaActaCalificacion.responsable.documento()}'
            url_archivo_a_firmar = eSolicitud.archivo.archivo.path
            x, y, numPage = obtener_coordenadas_firma_en_pdf(url_archivo_a_firmar, palabras)

            if not x or not y:
                raise NameError('No se encontró el responsable en el documento.')

            y += 50
            reason = f'Acta de calificaciones-{elimina_tildes(eMateria.nombre_completo())}'
            file_name = f"acta_calificaciones_{eMateria.id}_legalizada_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.pdf"
            nombre_repositorio = f'Acta de calificaciones firmada por {ePersona.nombre_completo()} de la materia (id: {eMateria.id}) {eMateria.nombre_completo()}'

            return {
                "x": x,
                "y": y,
                "numPage": numPage,
                "reason": reason,
                "file_name": file_name,
                "nombre_repositorio": nombre_repositorio,
                "eMateria": eMateria,
                "eRepositorioActaCalificacion": eRepositorioActaCalificacion,
                "eFirmaActaCalificacion": eFirmaActaCalificacion
            }

        def crear_solicitud_firmada(eSolicitud, eRepositorio):
            try:
                eSolicitudFirmada = SolicitudFirmada.objects.get(solicitud=eSolicitud)
            except SolicitudFirmada.DoesNotExist:
                eSolicitudFirmada = SolicitudFirmada(solicitud=eSolicitud)

            eSolicitudFirmada.archivo = eRepositorio
            eSolicitudFirmada.fechahora = datetime.now()
            eSolicitudFirmada.save(request)

            eSolicitud.estado = Solicitud.Estados.FIRMADO
            eSolicitud.save(request)

        with transaction.atomic():
            try:
                f = None
                data = {}
                addUserData(request, data)
                ePersona = data['persona']
                id = request.POST.get('id', 0)
                eSolicitud = obtener_solicitud(id)
                verificar_archivo_solicitud(eSolicitud)
                f = FirmaECForm(request.POST, request.FILES)
                if not f.is_valid():
                    raise NameError("Formulario incorrecto")
                password = f.cleaned_data['password']
                firma = request.FILES["firma"]
                bytes_certificado = firma.read()
                extension_certificado = os.path.splitext(firma.name)[1][1:]
                firma_data = None
                if eSolicitud.tipo == Solicitud.Tipos.ACTA_CALIFICACION:
                    # Firmar acta de calificaciones
                    firma_data = firmar_acta_calificaciones(ePersona, eSolicitud, f)
                if firma_data is None:
                    raise NameError(u"No se encontro datos de la firma")
                with open(eSolicitud.archivo.archivo.path, 'rb') as file:
                    archivo_a_firmar = file.read()

                datau = MY_JavaFirmaEc(
                    archivo_a_firmar=archivo_a_firmar,
                    archivo_certificado=bytes_certificado,
                    extension_certificado=extension_certificado,
                    password_certificado=password,
                    page=firma_data["numPage"],
                    reason=firma_data["reason"],
                    lx=str(firma_data["x"]),
                    ly=str(firma_data["y"]),
                ).sign_and_get_content_bytes()

                archivo_a_firmar = io.BytesIO(datau)
                archivo_a_firmar.seek(0)
                file_obj = DjangoFile(archivo_a_firmar, name=f"{remover_caracteres_especiales_unicode(firma_data['file_name'])}.pdf")

                eRepositorio = Repositorio(nombre=firma_data["nombre_repositorio"],
                                           tipo=Repositorio.Tipos.PDF,
                                           archivo=file_obj)
                eRepositorio.save(request)
                if eSolicitud.tipo == Solicitud.Tipos.ACTA_CALIFICACION:
                    # Guardar la firma en el repositorio de actas
                    eMateria = firma_data['eMateria']
                    eRepositorioActaCalificacion = firma_data['eRepositorioActaCalificacion']
                    eFirmaActaCalificacion = firma_data['eFirmaActaCalificacion']
                    eFirmaActaCalificacion.fecha = datetime.now()
                    eFirmaActaCalificacion.subido = True
                    eFirmaActaCalificacion.archivo = eRepositorio
                    eFirmaActaCalificacion.save(request)

                    # Crear solicitud siguiente, si aplica
                    eRepositorioActaCalificacion = eMateria.mi_repositorio_acta_calificacion()
                    eFirmaActaCalificacion_next = eRepositorioActaCalificacion.siguiente_a_firmar(responsable_actual_id=ePersona.id)
                    if eFirmaActaCalificacion_next:
                        eSolicitud_next = Solicitud(estado=Solicitud.Estados.PENDIENTE,
                                                    tipo=Solicitud.Tipos.ACTA_CALIFICACION,
                                                    descripcion=f"Solicitud de firma de acta de calificaciones por {ePersona.nombre_completo()} de la materia (id: {eMateria.id}) {eMateria.nombre_completo()}",
                                                    responsable=eFirmaActaCalificacion_next.responsable,
                                                    content_type=ContentType.objects.get_for_model(eMateria),
                                                    object_id=eMateria.id,
                                                    archivo=eRepositorio
                                                    )
                        eSolicitud_next.save(request)

                crear_solicitud_firmada(eSolicitud, eRepositorio)

                return JsonResponse({"isSuccess": True, "message": "Se firmó el acta correctamente"})
            except Exception as ex:
                transaction.set_rollback(True)
                print(f'Error on line {sys.exc_info()[-1].tb_lineno}: {str(ex)}')
                forms = f.toArray() if f else {}
                return JsonResponse({"isSuccess": False, "message": f"Error al procesar los datos: {str(ex)}", "forms": forms})

    @staticmethod
    def render_cancelar_solicitud(request:HttpRequest) -> JsonResponse:
        from firmaec.models import Solicitud, SolicitudCancelada, RepositorioActaCalificacion
        try:
            data = {}
            addUserData(request, data)
            ePersona = data['persona']
            id = request.POST.get('id', 0)
            try:
                eSolicitud = Solicitud.objects.get(pk=id)
            except ObjectDoesNotExist:
                raise NameError(u"No se encontro solicitud")
            if eSolicitud.tipo == Solicitud.Tipos.ACTA_CALIFICACION:
                eMateria = eSolicitud.content_object
                eRepositorioActaCalificacion = eMateria.mi_repositorio_acta_calificacion()
                eRepositorioActaCalificacion.estado = RepositorioActaCalificacion.Estados.Cancelada
                eRepositorioActaCalificacion.save(request)
            try:
                eSolicitudCancelada = SolicitudCancelada.objects.get(solicitud=eSolicitud)
            except ObjectDoesNotExist:
                eSolicitudCancelada = SolicitudCancelada(solicitud=eSolicitud)
            eSolicitudCancelada.fechahora = datetime.now()
            eSolicitudCancelada.observacion = f'Cancelado por la persona {ePersona.nombre_completo()}'
            eSolicitudCancelada.save(request)
            eSolicitud.estado = Solicitud.Estados.CANCELADO
            eSolicitud.save(request)
            return JsonResponse({"isSuccess": True, "message": "Se cancelo solicitud de firma"})
        except Exception as ex:
            transaction.set_rollback(True)
            print(f'Error on line {sys.exc_info()[-1].tb_lineno}: {str(ex)}')
            return JsonResponse({"isSuccess": False, "message": f"Error al procesar los datos: {str(ex)}"})
