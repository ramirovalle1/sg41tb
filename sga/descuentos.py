from datetime import datetime, timedelta
import json
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
from settings import TIPO_MORA_RUBRO
from sga.commonviews import addUserData
from sga.forms import ChequeProtestadoForm, ChequeFechaCobroForm
from sga.models import Factura, PagoCheque, ChequeProtestado, InscripcionFlags, TipoOtroRubro, Rubro, RubroOtro, RubroNotaDebito, Descuento, DetalleDescuento
from django.db import transaction
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
        if action=='protestar':
            try:
                cheque = PagoCheque.objects.get(pk=request.POST['id'])
                banco = cheque.banco
                f = ChequeProtestadoForm(request.POST)
                if f.is_valid():
                    #Preguntar si al menos tiene 1 pago ese cheque, si no es asi, es pq es un cheque protestado historico
                    inscripcion = cheque.pagos.all()[0].rubro.inscripcion

                    #Protestar el cheques
                    cheque.protestado=True
                    cheque.save()

                    #Marcar al estudiante en InscripcionFlag por tener cheque protestado
                    motivo = 'CHEQUE PROTESTADO: '+ cheque.numero
                    flag = InscripcionFlags(inscripcion=inscripcion,
                                            tienechequeprotestado=True,
                                            tienedeudaexterna=False,
                                            motivo=motivo)
                    flag.save()

                    #Generar Rubro de tipo Otro(Mora) por Cheque Protestado y con el valor de la tasa del banco correspondiente
                    descripcion = 'NOTA DE DEBITO (CHEQUE PROTESTADO): ' + cheque.numero + " - " + banco.nombre
                    hoy = datetime.now().today()
                    vence = hoy + timedelta(5) #Plazo de vencimiento de 5 dias
                    rubro = Rubro(fecha=hoy, valor=cheque.valor + banco.tasaprotesto,
                                  inscripcion=inscripcion, cancelado=False, fechavence=vence)
                    rubro.save()
                    # rubrootro = RubroNotaDebito(rubro=rubro, motivo=descripcion)
                    # OCastillo agrego enlace de chequeprotestado a nota de debito generada
                    rubrootro = RubroNotaDebito(rubro=rubro, motivo=descripcion,pagocheque=cheque)
                    rubrootro.save()

                    # Log de ADICIONADO RUBRO NOTA DE DEBITO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(rubrootro).pk,
                        object_id       = rubrootro.id,
                        object_repr     = force_str(rubrootro),
                        action_flag     = ADDITION,
                        change_message  = 'Creada Nota Debito' )

                    #Siempre se crea Registro en Modelo de Cheques Protestados
                    cheque_protestado = ChequeProtestado(cheque=cheque, motivo=f.cleaned_data['motivo'],fecha=datetime.now())
                    cheque_protestado.save()

                    # Log de CREACION CHEQUE PROTESTADO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(cheque_protestado).pk,
                        object_id       = cheque_protestado.id,
                        object_repr     = force_str(cheque_protestado),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Cheque Protestado')
            except:
                transaction.set_rollback(True)

        elif action=='fechacobro':
            cheque = PagoCheque.objects.get(pk=request.POST['id'])
            f = ChequeFechaCobroForm(request.POST)
            if f.is_valid():
                if cheque.fecha <= f.cleaned_data['fechacobro']:
                    fechacobro = f.cleaned_data['fechacobro']
                    cheque.fechacobro = fechacobro
                    cheque.save()
                    return HttpResponseRedirect("/cheques")
                else:
                    return HttpResponseRedirect("/cheques?action=fechacobro&id="+str(cheque.id)+"&error=1")

        return HttpResponseRedirect("/cheques")

    else:


        data = {'title': 'Listado de Descuentos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='detalle':
                data = {}
                data['detalle'] = DetalleDescuento.objects.filter(descuento__id=request.GET['id'])
                data['descuento'] = Descuento.objects.get(pk=request.GET['id'])
                return render(request ,"descuento/detalle.html" ,  data)

        else:
            search = None
            if 's' in request.GET:
                search = request.GET['s']
            if search:
                descuentos = Descuento.objects.filter(Q(inscipcion__persona__apellido1__icontains=search) | Q(inscipcion__persona__apellido2__icontains=search) | Q(inscipcion__persona__nombres__icontains=search)).order_by('fecha')
            else:
                descuentos = Descuento.objects.all().order_by('-fecha')
            paging = MiPaginador(descuentos, 100)
            p=1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(p)
            data['paging'] = paging
            data['rangospaging'] = paging.rangos_paginado(p)
            data['page'] = page
            data['search'] = search if search else ""
            data['descuentos'] = page.object_list
            return render(request ,"descuento/descuento.html" ,  data)
