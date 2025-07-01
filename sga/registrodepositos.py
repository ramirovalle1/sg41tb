import json
import os
from datetime import datetime
from django.contrib.admin.models import LogEntry, ADDITION, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
import xlrd
import xlwt
from decorators import secure_module
from settings import MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import DepositoArchivoForm, DetalleRegistroDepositoForm
from sga.models import RegistrosDepositos, CuentaBanco, DetalleRegistroDeposito, convertir_fecha, TituloInstitucion, elimina_tildes
from sga.registros import MiPaginador


# @login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
def view(request):
    print('ENTRO')
    if request.method=='POST':
        action = request.POST['action']
        if action == 'addarchivo':
            registro = None
            cont = 0
            try:
                if 'archivo' in request.FILES:
                    archivo = request.FILES['archivo']
                    cuentabancaria=CuentaBanco.objects.filter(id=request.POST['cuenta'])[:1].get()
                    if RegistrosDepositos.objects.filter(fecha=request.POST['fecha'],cuentabancaria=cuentabancaria).exists():
                        return HttpResponse(json.dumps({"result": "bad", "error": 'ya existe un registro para esa cuenta en esa fecha'}),content_type="application/json")
                    registro = RegistrosDepositos(fechasubida=datetime.now().date(),
                                                    cuentabancaria=cuentabancaria,
                                                    archivo=archivo,
                                                    fecha=request.POST['fecha'])

                    registro.save()
                    book = xlrd.open_workbook(MEDIA_ROOT + '/' + str(registro.archivo))
                    sh = book.sheet_by_index(0)
                    c = 0
                    ref = 0
                    val = 0
                    fr = 0
                    fec = ''
                    fec2 = 0
                    de= 0
                    tipo= 0
                    nut= 0
                    conc= 0
                    for rw in range(sh.nrows):
                        filaex = sh.row(rw)
                        if int(rw) == 0:
                            for f in filaex:
                                if 'FechaContable' in f.value:
                                    fec = c
                                if 'Valor' in f.value:
                                    val = c
                                if 'Numero' in f.value:
                                    ref = c
                                if 'FechaReal' in f.value:
                                    fr = c
                                if 'TipoMov' in f.value:
                                    tipo = c
                                if 'Nut' in f.value:
                                    nut = c
                                if 'Concepto' in f.value:
                                    conc = c
                                if 'Documento' in f.value:
                                    ref=c
                                if 'Monto' in f.value:
                                    val=c
                                if 'Tipo' in f.value:
                                    tipo=c
                                if 'Concepto' in f.value:
                                    conc=c
                                if 'Fecha' in f.value:
                                    fec2=c
                                if 'Oficina' in f.value:
                                    ofi=c

                                c = c + 1
                        elif int(rw) > 0:  # Pasa el Excel a una tabla
                            cedula = ''
                            # if filaex[2].value == '116':
                            if str(filaex[val].value) != '':
                                if fec != '':
                                    if not DetalleRegistroDeposito.objects.filter(referencia=(filaex[ref].value).replace(" ",""), valor=filaex[val].value, tipo=filaex[tipo].value, nut=filaex[nut].value,fechareal=filaex[fr].value).exists():
                                        detregistro = DetalleRegistroDeposito(registro=registro,
                                                                         fecha=convertir_fecha((filaex[fec].value).replace("/",'-')),
                                                                         hora=(filaex[fr].value.split(" ")[1]),
                                                                         horasimple=str(filaex[fr].value.split(" ")[1]).replace(':',''),
                                                                         fechareal=convertir_fecha((filaex[fr].value.split(" ")[0]).replace("/",'-')).date(),
                                                                         referencia=(filaex[ref].value).replace(" ",""),
                                                                         valor=filaex[val].value,
                                                                         concepto=filaex[conc].value,
                                                                         nut=filaex[nut].value,
                                                                         tipo=filaex[tipo].value)
                                        detregistro.save()
                                        cont = cont + 1
                                else:
                                    concepto = filaex[conc].value
                                    tipot = ''
                                    if 'TRANS' in concepto:
                                        tipot = 'N/C'
                                    if 'DEP' in concepto:
                                        tipot = 'DEP'
                                    if not DetalleRegistroDeposito.objects.filter(referencia=(int(filaex[ref].value)), valor=float(str(filaex[val].value).replace('$','').replace(',','')), tipo=tipot, fechareal=convertir_fecha((filaex[fec2].value).replace("/",'-')).date()).exists():
                                        detregistro = DetalleRegistroDeposito(registro=registro,
                                                                         fecha=convertir_fecha((filaex[fec2].value).replace("/",'-')).date(),
                                                                         hora=datetime.now().time(),
                                                                         fechareal=convertir_fecha((filaex[fec2].value).replace("/",'-')).date(),
                                                                         referencia=(int(filaex[ref].value)),
                                                                         valor=float(str(filaex[val].value).replace('$','').replace(',','')),
                                                                         concepto=filaex[conc].value,
                                                                         tipo=tipot)
                                        detregistro.save()
                                        cont = cont + 1

                                client_address = ip_client_address(request)
                                # Log de ADICIONAR GRADUADO
                                LogEntry.objects.log_action(
                                    user_id=request.user.pk,
                                    content_type_id=ContentType.objects.get_for_model(detregistro).pk,
                                    object_id=detregistro.id,
                                    object_repr=force_str(detregistro),
                                    action_flag=ADDITION,
                                    change_message='Actualizado Archivo (' + client_address + ')')

                    return HttpResponse(json.dumps({"result": "ok", "cont": cont}),content_type="application/json")
            except Exception as e:
                print(e)
                if registro:
                    if os.path.exists(MEDIA_ROOT + '/' + str(registro.archivo)):
                        os.remove(MEDIA_ROOT + '/' + str(registro.archivo))
                    registro.delete()

                return HttpResponse(json.dumps({"result": "bad", "error": str(e)}),content_type="application/json")

        elif action =='eliminar':
            try:
                registro=RegistrosDepositos.objects.filter(pk=request.POST['id'])[:1].get()
                if DetalleRegistroDeposito.objects.filter(registro=registro,validado=True).exists():
                    return HttpResponse(json.dumps({"result": "bad", "error":'Ya existen registros validados'}),content_type="application/json")
                if registro.detalles():
                    registro.detalles().delete()
                client_address = ip_client_address(request)
                # Log de ADICIONAR GRADUADO
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(registro).pk,
                    object_id=registro.id,
                    object_repr=force_str(registro),
                    action_flag=DELETION,
                    change_message='Eliminado Archivo Depositos (' + client_address + ')')
                registro.delete()
                return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({"result": "bad", "error": str(e)}),content_type="application/json")
    else:
        try:
            print('OKKKA')
            data = {'title': 'Registro Despositos'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action == 'addregistro':
                    print(request.GET)
                    registro= RegistrosDepositos.objects.filter(pk=request.GET['id'])[:1].get()
                    data['registro']= registro
                    data['form'] = DetalleRegistroDepositoForm(initial={'fecha':datetime.now().date(), 'fechareal':datetime.now().date()})
                    return render(request ,"registrodepositos/addregistro.html" ,  data)

                elif action=='ver':
                    registro=RegistrosDepositos.objects.filter(pk=request.GET['id'])[:1].get()
                    if 'info' in request.GET:
                        data['info']= request.GET['info']
                    if 'op' in request.GET:
                        data['op']=request.GET['op']
                        if request.GET['op']=='p':
                            data['detalles']=registro.detalles().filter(validado=False).order_by('fechareal')
                        elif request.GET['op']=='dp':
                            try:
                                cabecera = registro
                                detalles = registro.detalles().filter(validado=False).order_by('fechareal')

                                titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on;align: vert centre')
                                titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                                titulo.font.height = 20 * 11
                                titulo2.font.height = 20 * 11
                                subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                                subtitulo.font.height = 20 * 10

                                wb = xlwt.Workbook()
                                ws = wb.add_sheet('RegDepositosPendientes', cell_overwrite_ok=True)

                                tit = TituloInstitucion.objects.all()[:1].get()
                                ws.write_merge(0, 0, 0, 11, tit.nombre, titulo2)
                                ws.write_merge(1, 1, 0, 11, 'Registro de depositos', titulo2)
                                ws.write_merge(2, 2, 0, 11, str(cabecera.cuentabancaria), titulo2)
                                ws.write_merge(3, 3, 0, 11, str(cabecera.fecha)+' Subido el: '+str(cabecera.fechasubida), titulo2)

                                ws.write(5, 0, "Fecha_Contable", titulo)
                                ws.write(5, 1, "Fecha_Real", titulo)
                                ws.write(5, 2, "Hora", titulo)
                                ws.write(5, 3, "Valor", titulo)
                                ws.write(5, 4, "Tipo", titulo)
                                ws.write(5, 5, "Concepto", titulo)
                                ws.write(5, 6, "Nut", titulo)
                                ws.write(5, 7, "Numero", titulo)
                                ws.write(5, 8, "Hora_Simple", titulo)
                                ws.write(5, 9, "Validado", titulo)

                                fila = 6
                                for d in detalles:
                                    ws.write(fila, 0, elimina_tildes(d.fecha))
                                    ws.write(fila, 1, elimina_tildes(d.fechareal))
                                    ws.write(fila, 2, elimina_tildes(d.hora))
                                    ws.write(fila, 3, elimina_tildes(d.valor))
                                    if d.tipo:
                                        ws.write(fila, 4, elimina_tildes(d.tipo))
                                    else:
                                        ws.write(fila, 4, '-')
                                    ws.write(fila, 5, elimina_tildes(d.concepto))
                                    if d.nut:
                                        ws.write(fila, 6, elimina_tildes(d.nut))
                                    else:
                                        ws.write(fila, 6, '-')
                                    ws.write(fila, 7, elimina_tildes(d.referencia))
                                    if d.horasimple:
                                        ws.write(fila, 8, elimina_tildes(d.horasimple))
                                    else:
                                        ws.write(fila, 8, '-')
                                    if d.validado:
                                        ws.write(fila, 9, 'Validado')
                                    else:
                                        ws.write(fila, 9, 'Pendiente')
                                    fila = fila+1

                                fila = fila + 2
                                nombre = 'registro_deposito_pendientes' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":", "") + '.xls'
                                wb.save(MEDIA_ROOT + '/reporteexcel/' + nombre)
                                return HttpResponse(json.dumps({"result": "ok", "url": "ube/media/reporteexcel/" + nombre}), content_type="application/json")

                            except Exception as ex:
                                print('ERROR: ' + str(ex))
                        else:
                            data['detalles'] = registro.detalles().filter(validado=True).order_by('fechareal')
                    else:
                        search=None
                        if 's' in request.GET:
                            search=request.GET['s']
                            data['detalles'] = registro.detalles().filter(Q(referencia=search)|Q(nut=search)|Q(horasimple=search)).order_by('fechareal')
                            data['search']=search
                        else:
                            if registro.detalles():
                                data['detalles'] = registro.detalles().order_by('fechareal')
                            else:
                                data['detalles']=''
                    data['registro']=registro
                    return render(request ,"registrodepositos/detalles.html" ,  data)

            else:
                search = None
                if 's' in request.GET:
                    registros = RegistrosDepositos.objects.filter().order_by('-fecha')
                else:
                    if 'cuenta' in request.GET:
                        cuentabanco = CuentaBanco.objects.filter(pk=request.GET['cuenta'])[:1].get()
                        data['cuenta']=int(request.GET['cuenta'])
                        registros = RegistrosDepositos.objects.filter(cuentabancaria=cuentabanco).order_by('-fecha')
                    else:
                        registros = RegistrosDepositos.objects.all().order_by('-fecha')
                paging = MiPaginador(registros, 30)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                        paging = MiPaginador(registros, 30)
                    page = paging.page(p)
                except:
                    page = paging.page(1)
                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['registros'] = page.object_list
                data['usuario'] = request.user
                data['form'] = DepositoArchivoForm(initial={'fecha':datetime.now().date()})

                data['cuentabanco']=CuentaBanco.objects.all()
                return render(request ,"registrodepositos/registros.html" ,  data)
        except Exception as ex:
            print(ex)

