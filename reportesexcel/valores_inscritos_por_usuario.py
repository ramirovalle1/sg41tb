from datetime import datetime,timedelta
import json
import xlrd
import xlwt
from decimal import Decimal
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.db.models import Sum
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, ASIG_VINCULACION, ASIG_PRATICA
from sga.commonviews import addUserData, ip_client_address
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, GestionExcelForm, InscripcionValoresForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, \
     RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, RubroMatricula, Pago, \
    RubroCuota, RubroInscripcion,InscripcionVendedor

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    desde = request.POST['desde']
                    hasta = request.POST['hasta']
                    persona=Persona.objects.filter(pk=request.POST['persona'])[:1].get()
                    fechai = convertir_fecha(desde)
                    fechaf = convertir_fecha(hasta)

                    nivelmalla= NivelMalla.objects.filter(pk=request.POST['nivelmalla'])[:1].get()

                    # OC 11-junio-2018 para usuario gvlopez presentar solamente informacion de canal 3
                    usuario=request.user
                    if not usuario.username=='gvlopez':
                        matriculados = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,nivel__nivelmalla=nivelmalla,inscripcion__fecha__gte=fechai,inscripcion__fecha__lte=fechaf,inscripcion__user=persona.usuario).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    else:
                        matriculados = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,nivel__nivelmalla=nivelmalla,inscripcion__fecha__gte=fechai,inscripcion__fecha__lte=fechaf,inscripcion__user=persona.usuario,inscripcion__promocion__id__in=(5,6)).order_by('inscripcion__user','inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    # matriculados = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,nivel__nivelmalla=nivelmalla,inscripcion__fecha__gte=fechai,inscripcion__fecha__lte=fechaf,inscripcion__user=persona.usuario).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')

                    total=matriculados.count()
                    m = 16
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on;align: wrap on, vert centre, horiz center')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, 'Valores de Estudiantes Inscritos por Usuario y Rango de Fechas',titulo2)
                    ws.write(3, 0,'Inscritos por: ' +persona.nombre_completo_inverso() , subtitulo)
                    ws.write(4, 0,'Desde:   ' +str(fechai.date()), subtitulo)
                    ws.write(5, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)
                    ws.write(6, 0,'Nivel Malla:   ' +nivelmalla.nombre, subtitulo)
                    fila = 9
                    com = 9
                    detalle = 3
                    columna=8
                    c=9
                    pagado_inscripcion=0
                    pagado_matri=0
                    telefono1=''
                    pagado_cuota=0
                    telefono2=''
                    vendedor=''

                    cab = 10
                    cabcuotas = RubroCuota.objects.filter(matricula__in=matriculados).order_by('cuota').distinct('cuota').values('cuota')
                    ws.write(8,0,"CEDULA",titulo)
                    ws.write_merge(8,8,1,3,"NOMBRES",titulo)
                    ws.write_merge(8,8,4,7,"CARRERA",titulo)
                    ws.write(8,8,"INSCRIPCION",titulo)
                    ws.write(8,9,"MATRICULA",titulo)
                    for rc in cabcuotas:

                        ws.write(8,cab,"CUOTA "+str(rc['cuota']),titulo)
                        cab = cab +1

                    ws.write(8,cab,"INICIO NIVEL",titulo)
                    ws.write(8,cab+1,"CONVENCIONAL",titulo)
                    ws.write(8,cab+2,"CELULAR",titulo)
                    ws.write(8,cab+3,"VENDEDOR",titulo)
                    ws.write(8,cab+4,"ARCHIVADOR",titulo)
                    ws.write(8,cab+5,"EMAIL",titulo)
                    ws.write(8,cab+6,"EMAIL2",titulo)
                    total_matricula=0
                    total_inscripcion=0
                    total_cuota=0
                    archivador=''

                    for matri in matriculados:
                        # print(matri)
                        pagado_inscripcion=0
                        pagado_matri=0
                        email=''
                        email2=''

                        if RubroInscripcion.objects.filter(rubro__inscripcion=matri.inscripcion).exists():
                            rb=RubroInscripcion.objects.filter(rubro__inscripcion=matri.inscripcion)[:1].get()
                            if rb.rubro.cancelado==True:
                                pagado_inscripcion=rb.rubro.valor
                            else:
                                pagado_inscripcion=Pago.objects.filter(rubro=rb.rubro).aggregate(Sum('valor'))['valor__sum']
                                if pagado_inscripcion==None:
                                    pagado_inscripcion=0

                            total_inscripcion=total_inscripcion+ pagado_inscripcion
                            if rb.rubro.adeudado() >0:
                                ws.write(fila,columna,pagado_inscripcion,subtitulo3)
                                ws.write(fila+1,columna,"Vence: "+str(rb.rubro.fechavence),subtitulo3)
                            else:
                                ws.write_merge(fila,fila+1,columna,columna,pagado_inscripcion,subtitulo3)
                        else:
                            ws.write_merge(fila,fila+1,columna,columna,"NO TIENE RUBRO",subtitulo3)

                        if RubroMatricula.objects.filter(matricula=matri).exists():
                            rb=RubroMatricula.objects.filter(matricula=matri)[:1].get()
                            if rb.rubro.cancelado==True:
                                pagado_matri=rb.rubro.valor
                            else:
                                pagado_matri=Pago.objects.filter(rubro=rb.rubro).aggregate(Sum('valor'))['valor__sum']
                                if pagado_matri==None:
                                    pagado_matri=0

                            total_matricula=total_matricula+ pagado_matri

                            if rb.rubro.adeudado() > 0:
                                ws.write(fila,columna+1,pagado_matri,subtitulo3)
                                ws.write(fila+1,columna+1,"Vence: "+str(rb.rubro.fechavence),subtitulo3)
                            else:
                               ws.write_merge(fila,fila+1,columna+1,columna+1,pagado_matri,subtitulo3)
                        else:
                            ws.write_merge(fila,fila+1,columna+1,columna+1,"NO TIENE RUBRO",subtitulo3)

                        # ws.write(fila,columna+1,pagado_matri,subtitulo3)

                        if RubroCuota.objects.filter(matricula=matri).exists():
                            cuota=0
                            numcuotas= RubroCuota.objects.filter(matricula=matri).order_by('cuota').distinct('cuota')
                            rubrocuota=RubroCuota.objects.filter(matricula=matri).order_by('cuota')
                            for n in numcuotas:

                                for rc in RubroCuota.objects.filter(matricula=matri,cuota=n.cuota).order_by('cuota'):
                                    pagado_cuota=0
                                    cuota=Rubro.objects.filter(pk=rc.rubro.id,inscripcion=matri.inscripcion)[:1].get()
                                    if cuota.cancelado==True:
                                        pagado_cuota=cuota.valor
                                    else:
                                        pagado_cuota=Pago.objects.filter(rubro=cuota).aggregate(Sum('valor'))['valor__sum']
                                        if pagado_cuota==None:
                                            pagado_cuota=0

                                    total_cuota=total_cuota+ pagado_cuota
                                    if rc.rubro.adeudado()> 0:
                                        ws.write(fila,columna+2,str(pagado_cuota),subtitulo3)
                                        ws.write(fila+1,columna+2," Vence: " +str(rc.rubro.fechavence),subtitulo3)
                                    else:
                                        ws.write_merge(fila,fila+1,columna+2,columna+2,str(pagado_cuota),subtitulo3)
                                    columna=columna+1
                        ws.write_merge(fila,fila+1,cab,cab,str(matri.nivel.inicio),subtitulo3)

                        if matri.inscripcion.persona.cedula:
                            identificacion=matri.inscripcion.persona.cedula
                        else:
                            identificacion=matri.inscripcion.persona.pasaporte

                        if matri.inscripcion.persona.telefono_conv:
                            telefono1=matri.inscripcion.persona.telefono_conv
                        else:
                            telefono1=''

                        try:
                            if matri.inscripcion.persona.telefono:
                                telefono2=str(matri.inscripcion.persona.telefono)
                        except Exception as t:
                            telefono2=''

                        # OCU 27-04-2018 se agrega vendedor
                        if matri.inscripcion.vendedor():
                            vendedor=InscripcionVendedor.objects.filter(inscripcion=matri.inscripcion).get()
                            vendedor=elimina_tildes(vendedor.vendedor.nombres)
                        else:
                            vendedor=''

                        # OCU 29-08-2018 incluir archivador
                        if matri.inscripcion.identificador:
                            archivador=matri.inscripcion.identificador
                        else:
                            archivador="NO TIENE"

                        ws.write_merge(fila,fila+1,cab+1,cab+1,str(telefono1),subtitulo3)
                        ws.write_merge(fila,fila+1,cab+2,cab+2,str(telefono2),subtitulo3)

                        ws.write_merge(fila,fila+1,cab+3,cab+3,vendedor,subtitulo3)
                        ws.write_merge(fila,fila+1,cab+4,cab+4,archivador,subtitulo3)

                        try:
                            if matri.inscripcion.persona.email:
                                email=str(matri.inscripcion.persona.email)
                        except Exception as t:
                            email=''

                        try:
                            if matri.inscripcion.persona.emailinst:
                                email2=str(matri.inscripcion.persona.emailinst)
                        except Exception as t:
                            email2=''

                        ws.write_merge(fila,fila+1,cab+5,cab+5,email,subtitulo3)
                        ws.write_merge(fila,fila+1,cab+6,cab+6,email2,subtitulo3)
                        ws.write_merge(com, fila+1,0,0, str(identificacion) , subtitulo3)
                        ws.write_merge(com, fila+1,1,3,elimina_tildes(matri.inscripcion.persona.nombre_completo_inverso()), subtitulo3)
                        ws.write_merge(com, fila+1,4,7,elimina_tildes(matri.inscripcion.carrera), subtitulo3)

                        com=fila+2
                        fila = fila +2
                        columna=8
                    ws.write_merge(com, fila,0,3, "TOTALES:" ,titulo2)
                    ws.write_merge(com,fila,4,5,str(total) +" Estudiantes",titulo2)
                    ws.write(fila,columna,total_inscripcion,titulo2)
                    ws.write(fila,columna+1,total_matricula,titulo2)
                    ws.write(fila,columna+2,total_cuota,titulo2)

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='valores_inscritos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+" "+str(matri)}),content_type="application/json")

        else:
            data = {'title': 'Valores de Inscritos por Usuario'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=InscripcionValoresForm(initial={'desde':datetime.now().date(),'hasta':datetime.now().date()})
                return render(request ,"reportesexcel/valores_inscritos.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

