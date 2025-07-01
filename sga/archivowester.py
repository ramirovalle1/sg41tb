from decimal import Decimal
import os
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.forms import model_to_dict
from django.utils.encoding import force_str
import xlrd
import xlwt
from sga.models import Oficio, PagoWester,Inscripcion, ArchivoWester, Rubro, elimina_tildes,Matricula,Periodo,EvaluacionProfesor,DatoInstrumentoEvaluacion,Profesor,CalificacionEvaluacion, RegistroWester, TipoIncidencia
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from sga.commonviews import addUserData, ip_client_address
from django.template import RequestContext
from sga.forms import TipoMedicamentoForm, TipoOficioForm, OficioForm, PagoWesterForm, ArchivoWesterForm
from datetime import datetime, date, timedelta
from django.db.models import Q, Avg
from settings import EMAIL_ACTIVE, MEDIA_ROOT, SITE_ROOT, INCIDENCIA_FACT, HABILITA_APLICA_DESCUE
from sga.tasks import send_html_mail
from decorators import secure_module


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
# @transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'generar':
                if not ArchivoWester.objects.filter(fecha=datetime.now()).exists():
                    try:
                        matricula = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,nivel__cerrado=False).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                        titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                        titulo.font.height = 20*11
                        subtitulo = xlwt.easyxf(num_format_str="@")
                        # subtitulo.font.height = 20*10
                        # style1 = xlwt.easyxf('')
                        wb = xlwt.Workbook()
                        ws = wb.add_sheet('Hoja1',cell_overwrite_ok=True)
                        cont =-1
                        no_ruc = open(os.path.join(MEDIA_ROOT, 'error.txt'), 'w')
                        for m in matricula:
                            try:
                                # print(m)
                                fec=datetime.now().date()
                                fec=datetime.now().date()  + timedelta(days=30)
                                # fec=date(fec.year,fec.month+1,1) - timedelta(days=1)
                                if m.inscripcion.persona.cedula or  m.inscripcion.persona.pasaporte:
                                    for r in Rubro.objects.filter(inscripcion=m.inscripcion,cancelado=False,fechavence__lte=fec,valor__gt=0).order_by('cancelado','fechavence'):
                                        cont =cont +1
                                        # print((cont))
                                        adeuda=0
                                        if HABILITA_APLICA_DESCUE:
                                            if r.aplicadescuento(None)[1] > 0:
                                                adeuda = str(Decimal(r.aplicadescuento(None)[0]).quantize(Decimal(10) ** -2)).replace(",",".")
                                            else:
                                                adeuda = str(Decimal(r.adeudado()).quantize(Decimal(10)**-2)).replace(",",".")
                                        else:
                                            adeuda = str(Decimal(r.adeudado()).quantize(Decimal(10)**-2)).replace(",",".")
                                        adeuda_d= Decimal(adeuda)
                                        if adeuda_d > 0:
                                            if m.inscripcion.persona.cedula:
                                                ws.write(cont, 0, str(m.inscripcion.persona.cedula),subtitulo)
                                            else:
                                                ws.write(cont, 0, str(m.inscripcion.persona.pasaporte),subtitulo)

                                            try:
                                                nombrecompleto = m.inscripcion.persona.nombre_completo_inverso()
                                            except Exception as e:
                                                nombrecompleto = str(elimina_tildes(m.inscripcion.persona.nombre_completo()))
                                            ws.write(cont, 1, nombrecompleto,subtitulo)
                                            # ws.row(cont).set_cell_text()
                                            if HABILITA_APLICA_DESCUE:
                                                adeuda = str(Decimal(r.aplicadescuento(None)[0]).quantize(Decimal(10) ** -2)).replace(",",".")
                                            else:
                                                adeuda = str(Decimal(r.adeudado()).quantize(Decimal(10)**-2)).replace(",",".")
                                            ws.write(cont, 2, adeuda,subtitulo)
                                            ws.write(cont, 3,"0.00",subtitulo)
                                            ws.write(cont, 4,"0.00",subtitulo)
                                            try:
                                                fecha2=datetime(int(datetime.now().date().year+1) ,r.fechavence.month,r.fechavence.day).date()
                                            except :
                                                r.fechavence = r.fechavence - timedelta(1)
                                                fecha2=datetime(int(datetime.now().date().year+1) ,r.fechavence.month,r.fechavence.day).date()
                                            ws.write(cont, 5,str(fecha2).replace('-',''),subtitulo)
                                            #OCastillo 26-07-2022 campo hora de vencimiento
                                            ws.write(cont, 6,"23:59",subtitulo)
                                            ws.write(cont, 7,r.id,subtitulo)
                                            try:
                                                nombrerubro = r.nombre()[:100]
                                            except:
                                                nombrerubro = elimina_tildes(r.nombre()[:100])
                                            ws.write(cont, 8,nombrerubro,subtitulo)
                                else:
                                    no_ruc.write(str(m.inscripcion) + '\n')
                            except Exception as ex:
                                mail_errores(str(m.inscripcion),ex)
                                pass
                        no_ruc.close()
                        # nombre fechanueva=datetime.now().date() + timedelta(days=1) ='clientes'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                        fechanueva=datetime.now().date() + timedelta(days=1)
                        nombre ='141'+str(fechanueva.year)+str(fechanueva.month).zfill(2)+str(fechanueva.day).zfill(2)+'.xls'
                        wb.save(MEDIA_ROOT+'/archivowester/'+nombre)
                        archivow = ArchivoWester(fecha=datetime.now(),
                                                 archivo="/media/archivowester/"+nombre)
                        archivow.save()
                        return HttpResponse(json.dumps({"result":"ok", "url": "/media/archivowester/"+nombre}),content_type="application/json")
                    except Exception as ex:
                        print(("ocurrio un error " + str(ex)))
                        return HttpResponse(json.dumps({"result":str(ex + " "+ str(m.inscripcion.persona.nombre_completo()))}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"Ya Existe un Arcivo en esta fecha"}),content_type="application/json")
            elif action == 'addarchivowester':
                f = ArchivoWesterForm(request.POST,request.FILES)
                if f.is_valid():
                    archivow = ArchivoWester.objects.get(id=request.POST['idarc'])
                    if 'archivo' in request.FILES:
                        archivo = request.FILES['archivo']
                        # if inscripficha.croquis :
                        #     mensaje = 'Editado'
                        #     if (MEDIA_ROOT + '/' + str(inscripficha.croquis)) and archivo:
                        #         os.remove(MEDIA_ROOT + '/' + str(inscripficha.croquis))
                        # else:
                        #     mensaje = 'Adicionado'
                        archivow.archivowester = archivo
                        archivow.save()
                        book = xlrd.open_workbook(SITE_ROOT + archivow.archivowester.url)
                        sh = book.sheet_by_index(0)
                        for rw in range(sh.nrows):
                           filaex = sh.row(rw)

                           fecha = date(int(str(filaex[0].value).replace(".","")[0:4]),int(str(filaex[0].value).replace(".","")[4:6]),int(str(filaex[0].value).replace(".","")[6:8]))
                           if filaex[6].value == 'Activo':
                               if not 'C' in filaex[3].value:
                                   if not 'O' in filaex[3].value:
                                       registro = RegistroWester(archivo=archivow,
                                                                 fecha=fecha,
                                                                 hora=filaex[1].value,
                                                                 codigo=filaex[2].value,
                                                                 cedula=filaex[5].value,
                                                                 valor=filaex[4].value,
                                                                 cuenta = filaex[3].value,
                                                                 estado = filaex[6].value)
                                       registro.save()
                                       if PagoWester.objects.filter(codigo=registro.codigo).exclude(factura=None).exists():
                                           registro.facturado =True
                                           registro.save()
                                           # fecha = filaex[0]
                                           # hora = filaex[1]
                                           # codigo = filaex[2]
                                           # cedula  = filaex[3]
                                           # valor  = filaex[4]
                                           # rubro  = filaex[5]

                        client_address = ip_client_address(request)
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(archivow).pk,
                            object_id       = archivow.id,
                            object_repr     = force_str(archivow),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionado Archivo de W.U (' + client_address + ')' )

                    return HttpResponseRedirect('/archivowester')
                else:
                    return HttpResponseRedirect('/archivowester?error=el archivo no tiene el formato correcto')


            elif action == 'eliminar':
                try:

                    archivo = ArchivoWester.objects.filter(pk=request.POST['id'])[:1].get()
                    archivo.archivowester = ''
                    archivo.save()
                    mensaje = 'Eliminar Archivo Wester'
                    client_address = ip_client_address  (request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(archivo).pk,
                        object_id       = archivo.id,
                        object_repr     = force_str(archivo),
                        action_flag     = CHANGE,
                        change_message  = mensaje+' (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action=='eliminarregistro':
                result={}
                try:
                    if ArchivoWester.objects.filter(pk=request.POST['idregistro']).exists():
                        ar=ArchivoWester.objects.filter(pk=request.POST['idregistro'])[:1].get()
                        if RegistroWester.objects.filter(archivo=ar,facturado=False):
                            for re in RegistroWester.objects.filter(archivo=ar,facturado=False):
                                if not re.esta_facturado():
                                    re.delete()
                            mensaje = 'Eliminar Registro de Wester '
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(ar).pk,
                            object_id       = ar.id,
                            object_repr     = force_str(ar),
                            action_flag     = DELETION,
                            change_message  = mensaje+' (' + client_address + ')' )

                            result['result']  = "ok"
                            ar.archivowester=None
                            ar.save()
                            return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as e:
                    result['result']  = str(e)
                    return HttpResponse(json.dumps(result), content_type="application/json")

        else:
            data = {'title': 'Registro de Pagos'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action =='ver':
                    data['registros']=RegistroWester.objects.filter(archivo__id=request.GET['id'])
                    data['archivowester']=ArchivoWester.objects.filter(pk=request.GET['id'])[:1].get()
                    search = None
                    todos = None
                    facturado = None
                    if 'error' in request.GET:
                        data['error'] = request.GET['error']

                    if 's' in request.GET:
                        search = request.GET['s']
                    if 'pen' in request.GET:
                        facturado = False
                        data['pen'] =1
                    if 'fac' in request.GET:
                        facturado = True
                        data['fac'] =1
                    if 't' in request.GET:
                        todos = request.GET['t']
                    if search:
                        registros = RegistroWester.objects.filter(Q(codigo=search)|Q(cedula=search),archivo__id=request.GET['id'])
                    elif facturado != None:
                        registros =RegistroWester.objects.filter(archivo__id=request.GET['id'],facturado=facturado)
                    else:
                        registros =RegistroWester.objects.filter(archivo__id=request.GET['id'])

                    paging = MiPaginador(registros, 30)
                    p = 1
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
                    data['todos'] = todos if todos else ""
                    data['registros'] = page.object_list
                    data['frmarchivowester'] = ArchivoWesterForm()

                    if 'id' in request.GET:
                        data['id'] = request.GET['id']
                    return render(request ,"archivowester/registroarchivo.html" ,  data)

            else:
                search = None
                todos = None
                if 'error' in request.GET:
                    data['error'] = request.GET['error']

                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    archivo = ArchivoWester.objects.filter(fecha=convertir_fecha(search)).order_by('-fecha')
                else:

                    archivo = ArchivoWester.objects.all().order_by('-fecha')
                if ArchivoWester.objects.filter(fecha=datetime.now()).exists():
                    data['ban'] = 1

                paging = MiPaginador(archivo, 30)
                p = 1
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
                data['todos'] = todos if todos else ""
                data['archivo'] = page.object_list
                data['frmarchivowester'] = ArchivoWesterForm()
                return render(request ,"archivowester/registro.html" ,  data)
    except Exception as e:
        return HttpResponseRedirect("/archivowester")

def convertir_fecha(s):
    try:
        return datetime(int(s[-4:]), int(s[3:5]), int(s[:2]))
    except:
        return datetime.now()


def mail_errores(persona,error):
    if TipoIncidencia.objects.filter(pk=INCIDENCIA_FACT).exists():
        tipo = TipoIncidencia.objects.get(pk=INCIDENCIA_FACT)
        hoy = datetime.now()
        contenido = "ERROR CREANDO REGISTRO"+' '+ persona
        send_html_mail("PROBLEMA CON CREACION DE ARCHIVO WESTER",
            "emails/westermail.html", { 'fecha': hoy,'contenido': contenido,'error':error},tipo.correo.split(","))
