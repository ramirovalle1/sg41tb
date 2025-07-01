from datetime import datetime
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import addUserData, ip_client_address
from sga.models import *

# @login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
def view(request):
    if request.method=='POST':
        pass
    else:
        data = {'title': 'Reporteria'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'factura_sri_comprobante':
                try:
                    fechamarzo = datetime.strptime('31-03-2024', '%d-%m-%Y').date()
                    data['fechamarzo']= fechamarzo
                    print(request.GET)
                    factura = Factura.objects.get(id=request.GET['id'])
                    data['factura'] = factura
                    data['hoy'] = datetime.now().date()
                    data['institucion'] = TituloInstitucion.objects.filter()[:1].get()
                    data['inscripcion'] = Pago.objects.filter(id__in=factura.pagos.all().values('id'))[:1].get().rubro.inscripcion
                    data['rubros'] = Rubro.objects.filter(pago__id__in=Pago.objects.filter(id__in=factura.pagos.all().values('id'))).order_by('fecha')
                    data['pago'] = Pago.objects.filter(id__in=factura.pagos.all())[:1].get()
                    return render(request ,"reporteria/factura_sri_comprobante.html" ,  data)
                except Exception as ex:
                    print(ex)

        else:
            pass