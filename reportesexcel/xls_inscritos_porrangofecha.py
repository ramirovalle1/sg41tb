from datetime import datetime,timedelta
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import DistributivoForm
from sga.models import Inscripcion, convertir_fecha, Factura, ClienteFactura, TituloInstitucion, ReporteExcel, \
    NotaCreditoInstitucion, Persona, TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, \
    AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, \
    RubroMatricula, Pago, RubroCuota, RubroInscripcion, InscripcionVendedor, InscripcionGrupo, \
    ViewInscripcionesOnline, ViewCrmProspectosMat, EntregaUniformeAdmisiones
from fpdf import FPDF
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action =='generarexcel':
                try:
                    desde = request.POST['desde']
                    hasta = request.POST['hasta']
                    fechai = convertir_fecha(desde)
                    fechaf = convertir_fecha(hasta)

                    # OC 11-junio-2018 para usuario gvlopez presentar solamente informacion de canal 3
                    usuario=request.user
                    if not usuario.username=='gvlopez':
                        # inscritos = Inscripcion.objects.filter(pk=52626,persona__usuario__is_active=True,fecha__gte=fechai,fecha__lte=fechaf,carrera__carrera=True).order_by('user','persona__apellido1','persona__apellido2')
                        inscritos = Inscripcion.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,carrera__carrera=True).order_by('user','persona__apellido1','persona__apellido2')
                    else:
                        # matriculados = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,nivel__nivelmalla=nivelmalla,inscripcion__fecha__gte=fechai,inscripcion__fecha__lte=fechaf,inscripcion__promocion__id__in=(5,6)).order_by('inscripcion__user','inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                        inscritos = Inscripcion.objects.filter(fecha__gte=fechai,fecha__lte=fechaf,carrera__carrera=True,inscripcion__promocion__id__in=(5,6)).order_by('user','persona__apellido1','persona__apellido2')

                    #print(inscritos)

                    total_inscritos=0
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
                    ws.write_merge(1, 1,0,m, 'Valores de Estudiantes Inscritos por Rango de Fechas',titulo2)
                    ws.write(4, 0,'Desde:   ' +str(fechai.date()), subtitulo)
                    ws.write(5, 0,'Hasta:   ' +str(fechaf.date()), subtitulo)

                    fila = 9
                    com = 9
                    detalle = 3
                    columna=12
                    c=9
                    pagado_inscripcion=0
                    pagado_matri=0
                    telefono1=''
                    pagado_cuota=0
                    telefono2=''
                    cab = 18
                    inscritopor=''
                    inscrito=''
                    promocion=''
                    vendedor=''

                    # cabcuotas = RubroCuota.objects.filter(matricula__in=matriculados).order_by('cuota').distinct('cuota').values('cuota')
                    cabcuotas = RubroCuota.objects.filter(matricula__inscripcion__in=inscritos,matricula__nivel__cerrado=False).order_by('cuota').distinct('cuota').values('cuota')
                    ws.write(8,0,"CEDULA",titulo)
                    ws.write_merge(8,8,1,3,"NOMBRES",titulo)
                    ws.write_merge(8,8,4,7,"CARRERA",titulo)

                    ws.write(8,8,"Paralelo",titulo)
                    ws.write(8,9,"Fecha Inscripcion",titulo)
                    ws.write(8,10,"Matriculado",titulo)
                    ws.write(8,11,"Fecha Matricula",titulo)
                    ws.write(8,12,"INSCRIPCION",titulo)
                    ws.write(8,13,"Vence Inscripcion",titulo)
                    ws.write(8,14,"MATRICULA",titulo)
                    ws.write(8,15,"Vence Matricula",titulo)
                    ws.write(8,16, "Tipo Persona", titulo)
                    ws.write(8,17, "Via", titulo)

                    for rc in cabcuotas:
                        ws.write(8,cab,"CUOTA "+str(rc['cuota']),titulo)
                        ws.write(8,cab+1,"Vencimiento CUOTA "+str(rc['cuota']),titulo)
                        cab = cab +2

                    ws.write(8,cab,"INICIO NIVEL",titulo)
                    ws.write(8,cab+1,"CONVENCIONAL",titulo)
                    ws.write(8,cab+2,"CELULAR",titulo)
                    ws.write_merge(8,8,cab+3,cab+5,"INSCRITO POR",titulo)
                    ws.write_merge(8,8,cab+6,cab+8,"EMAIL INST",titulo)
                    ws.write_merge(8,8,cab+9,cab+11,"EMAIL PERSONAL",titulo)
                    ws.write_merge(8,8,cab+12,cab+12,"PROMOCION",titulo)
                    ws.write_merge(8,8,cab+13,cab+13,"VENDEDOR",titulo)
                    ws.write_merge(8,8,cab+14,cab+14,"JUGUETE/CANASTA",titulo)
                    ws.write_merge(8,8,cab+15,cab+15, 'DESCUENTO CUOTAS', titulo)
                    ws.write_merge(8,8,cab+16,cab+16, 'CONV. INSTITUCIONAL', titulo)
                    ws.write(8,cab+17, 'SEGMENTO', titulo)
                    ws.write(8,cab+18, 'DETALLE DE SEGMENTO', titulo)
                    ws.write(8,cab+19, 'USUARIO ACTIVO', titulo)
                    ws.write(8,cab+20, 'COLEGIO', titulo)
                    ws.write(8,cab+21, 'EN ONLINE', titulo)
                    ws.write(8,cab+22, 'PROVINCIA NACIMIENTO', titulo)
                    ws.write(8,cab+23, 'CANTON NACIMIENTO', titulo)
                    ws.write(8,cab+24, 'PROVINCIA RESIDENCIA', titulo)
                    ws.write(8,cab+25, 'CANTON RESIDENCIA', titulo)
                    ws.write(8,cab+26, 'CIUDAD RESIDENCIA', titulo)
                    ws.write(8,cab+27, 'SECTOR RESIDENCIA', titulo)
                    ws.write(8,cab+28, 'MODALIDAD', titulo)
                    ws.write(8,cab+29, 'TALLA UNIFORME', titulo)
                    ws.write(8,cab+30, 'ANUNCIO', titulo)

                    total_matricula=0
                    total_inscripcion=0
                    total_cuota=0
                    fecha_matricula=''
                    inscri=None
                    juguete=''
                    from django.db import connection
                    cur = connection.cursor()
                    cur.execute("REFRESH MATERIALIZED VIEW view_crmprospectos_mat; REFRESH MATERIALIZED VIEW view_inscripcionesonline;")
                    try:
                        connection.commit()
                    except Exception as e:
                        print("Error al actualizar la vista materializada view_crmprospectos_mat:", str(e))
                        connection.rollback()
                    for inscri in inscritos:
                        print(inscri)
                        estado=''
                        fecha_matricula=''
                        matri=''
                        desc_cuotas=0
                        convenio=''
                        total_inscritos=total_inscritos+1
                        if Matricula.objects.filter(inscripcion=inscri,inscripcion__persona__usuario__is_active=True,nivel__cerrado=False,inscripcion__fecha__gte=fechai,inscripcion__fecha__lte=fechaf).exists():
                            matri= Matricula.objects.filter(inscripcion=inscri,inscripcion__persona__usuario__is_active=True,nivel__cerrado=False)[:1].get()
                            fecha_matricula=matri.fecha
                            estado='Si'
                            grupo_id = inscri.grupo().id
                            rbi = RubroInscripcion.objects.filter(rubro__inscripcion=inscri).first()
                            if rbi:
                                if rbi.rubro.cancelado==True:
                                    pagado_inscripcion=rbi.rubro.valor
                                else:
                                    pagado_inscripcion=Pago.objects.filter(rubro=rbi.rubro).aggregate(Sum('valor'))['valor__sum']
                                    if pagado_inscripcion==None:
                                        pagado_inscripcion=0

                                total_inscripcion=total_inscripcion+ pagado_inscripcion
                                if rbi.rubro.adeudado() >0:
                                    ws.write(fila,columna,pagado_inscripcion,subtitulo3)
                                    ws.write(fila,columna+1,str(rbi.rubro.fechavence),subtitulo3)
                                else:
                                    ws.write_merge(fila,fila,columna,columna,pagado_inscripcion,subtitulo3)
                            else:
                                ws.write_merge(fila,fila,columna,columna,"NO TIENE RUBRO",subtitulo3)
                            # if ViewCrmProspectos.objects.filter(cedula=inscri.persona.cedula, fecharegistro__gte=fechai,fecharegistro__lte=fechaf, grupo_id=inscri.grupo().id).exists():
                            cedulap = inscri.persona.cedula
                            if ViewCrmProspectosMat.objects.filter(cedula=cedulap, grupo_id=grupo_id).exists():
                                try:
                                    # viewbasegestion = ViewCrmProspectos.objects.filter(cedula=inscri.persona.cedula, fecharegistro__gte=fechai,fecharegistro__lte=fechaf, grupo_id=inscri.grupo().id)[:1].get()
                                    viewbasegestion = ViewCrmProspectosMat.objects.filter(cedula=cedulap, grupo_id=grupo_id)[:1].get()
                                    ws.write(fila,columna+4, str(viewbasegestion.tipopersona))
                                    ws.write(fila,columna+5, str(viewbasegestion.via))
                                    if viewbasegestion.segmentoadmin:
                                        ws.write(fila, cab+17, str(viewbasegestion.segmentoadmin))
                                    else:
                                        ws.write(fila, cab+17, '')
                                    if viewbasegestion.nombresegmento:
                                        ws.write(fila, cab+18, str(viewbasegestion.nombresegmento))
                                    else:
                                        ws.write(fila, cab+18, '')
                                except:
                                    pass

                            if inscri.persona.usuario.is_active:
                                ws.write(fila, cab+19, 'SI')
                            else:
                                ws.write(fila, cab+19, 'NO')

                            if inscri.estcolegio:
                                ws.write(fila, cab+20, elimina_tildes(inscri.estcolegio.nombre))
                            else:
                                ws.write(fila, cab+20, '')
                            rbm=  RubroMatricula.objects.filter(matricula=matri).first()
                            if rbm:
                                if rbm.rubro.cancelado==True:
                                    pagado_matri=rbm.rubro.valor
                                else:
                                    pagado_matri=Pago.objects.filter(rubro=rbm.rubro).aggregate(Sum('valor'))['valor__sum']
                                    if pagado_matri==None:
                                        pagado_matri=0

                                total_matricula=total_matricula+ pagado_matri

                                if rbm.rubro.adeudado() > 0:
                                    ws.write(fila,columna+2,pagado_matri,subtitulo3)
                                    ws.write(fila,columna+3,str(rbm.rubro.fechavence),subtitulo3)
                                else:
                                   ws.write_merge(fila,fila,columna+2,columna+2,pagado_matri,subtitulo3)
                            else:
                                ws.write_merge(fila,fila,columna+2,columna+2,"NO TIENE RUBRO",subtitulo3)

                            if RubroCuota.objects.filter(matricula=matri).exists():
                                cuota=0
                                numcuotas= RubroCuota.objects.filter(matricula=matri).order_by('cuota').distinct('cuota')
                                rubrocuota=RubroCuota.objects.filter(matricula=matri).order_by('cuota')
                                for n in numcuotas:
                                    if len(numcuotas)==1:
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
                                                ws.write(fila,columna+6,pagado_cuota,subtitulo3)
                                                ws.write(fila,columna+7,str(rc.rubro.fechavence),subtitulo3)
                                            else:
                                                ws.write_merge(fila,fila,columna+6,columna+6,pagado_cuota,subtitulo3)
                                            columna=columna+1
                                    else:
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
                                                ws.write(fila,columna+6,pagado_cuota,subtitulo3)
                                                ws.write(fila,columna+7,str(rc.rubro.fechavence),subtitulo3)
                                            else:
                                                ws.write_merge(fila,fila,columna+6,columna+6,pagado_cuota,subtitulo3)
                                            columna=columna+2
                            ws.write_merge(fila,fila,cab,cab,str(matri.nivel.inicio),subtitulo3)
                        else:
                            estado='No matriculado'
                            fecha_matricula=''

                        if inscri.persona.cedula:
                            identificacion=inscri.persona.cedula
                        else:
                            identificacion=inscri.persona.pasaporte

                        try:
                            if inscri.persona.telefono_conv:
                                telefono1=inscri.persona.telefono_conv.replace("-","")
                            else:
                                telefono1=''
                            ws.write_merge(fila,fila,cab+1,cab+1,telefono1,subtitulo3)
                        except Exception as ex:
                            pass

                        try:
                            if inscri.persona.telefono:
                                telefono2=inscri.persona.telefono.replace("-","")
                            else:
                                telefono2=''
                            ws.write_merge(fila,fila,cab+2,cab+2,telefono2,subtitulo3)
                        except Exception as ex:
                            pass

                        try:
                            if inscri.persona.emailinst:
                                correo1=inscri.persona.emailinst
                            else:
                                correo1=''
                            ws.write_merge(fila,fila,cab+6,cab+8,correo1,subtitulo3)
                        except Exception as ex:
                            pass

                        try:
                            if inscri.persona.email:
                                correo2=inscri.persona.email
                            else:
                                correo2=''
                            ws.write_merge(fila,fila,cab+9,cab+11,correo2,subtitulo3)
                        except Exception as ex:
                            pass

                        if inscri.user:
                            inscritopor=inscri.user
                            inscritopor=Persona.objects.filter(usuario=inscritopor).first()
                            inscrito= elimina_tildes(inscritopor.nombre_completo_inverso())
                        else:
                            inscrito=''
                        ws.write_merge(com, fila,cab+3,cab+5,elimina_tildes(inscrito), subtitulo3)
                        if inscri.promocion:
                            promocion=inscri.promocion.descripcion
                        else:
                            promocion=''

                        if inscri.entregajuguetecanastas:
                            juguete='ENTREGADO'
                        else:
                            juguete=''

                        if inscri.descuentoporcent:
                            desc_cuotas = inscri.descuentoporcent
                        else:
                            desc_cuotas = 0

                        if inscri.vendedor():
                            vendedor=InscripcionVendedor.objects.filter(inscripcion=inscri)[:1].get()
                            vendedor=vendedor.vendedor.nombres
                        else:
                            vendedor=''

                        if inscri.empresaconvenio:
                            convenio =elimina_tildes(inscri.empresaconvenio.nombre)
                        else:
                            convenio = ''

                        ws.write_merge(com, fila,0,0, str(identificacion) , subtitulo3)
                        ws.write_merge(com, fila,1,3,elimina_tildes(inscri.persona.nombre_completo_inverso()), subtitulo3)

                        ws.write_merge(com, fila,cab+12,cab+12,promocion, subtitulo3)
                        ws.write_merge(com, fila,cab+13,cab+13,elimina_tildes(vendedor), subtitulo3)
                        ws.write_merge(com, fila,cab+14,cab+14,str(juguete), subtitulo3)
                        ws.write_merge(com, fila,cab+15,cab+15,desc_cuotas, subtitulo3)
                        ws.write_merge(com, fila,cab+16,cab+16,convenio, subtitulo3)
                        if ViewInscripcionesOnline.objects.filter(cedula=inscri.persona.cedula).exists() or ViewInscripcionesOnline.objects.filter(pasaporte=inscri.persona.pasaporte).exclude(pasaporte='').exclude(pasaporte=None).exists():
                            ws.write(fila, cab+21, 'SI')
                        else:
                            ws.write(fila, cab+21, 'NO')

                        try:
                            ws.write(fila, cab+22, inscri.persona.provincia.nombre)
                        except:
                            ws.write(fila, cab+22, '')

                        try:
                            ws.write(fila, cab+23, inscri.persona.canton.nombre)
                        except:
                            ws.write(fila, cab+23, '')

                        try:
                            ws.write(fila, cab+24, inscri.persona.provinciaresid.nombre)
                        except:
                            ws.write(fila, cab+24, '')

                        try:
                            ws.write(fila, cab+25, inscri.persona.cantonresid.nombre)
                        except:
                            ws.write(fila, cab+25, '')

                        try:
                            if inscri.persona.ciudad:
                                ws.write(fila, cab+26, elimina_tildes(inscri.persona.ciudad))
                            else:
                                ws.write(fila, cab+26, '')
                        except:
                            ws.write(fila, cab+26, '')

                        try:
                            ws.write(fila, cab+27, inscri.persona.sectorresid.nombre)
                        except:
                            ws.write(fila, cab+27, '')

                        try:
                            ws.write(fila, cab+28, inscri.modalidad.nombre)
                        except:
                            ws.write(fila, cab+28, '')
                        try:
                            ws.write(fila, cab+30, inscri.anuncio.descripcion)
                        except:
                            ws.write(fila, cab+30, '')
                        # ENTREGA DE UNIFORME DE ADMISION VER TALLA
                        try:
                            entregauniforme = EntregaUniformeAdmisiones.objects.filter(inscripcion = inscri)[:1].get()
                            if entregauniforme:
                                ws.write(fila, cab+29, entregauniforme.talla.nombre if entregauniforme.talla.nombre else '')
                        except:
                            ws.write(fila, cab + 29, '')

                        ws.write_merge(com, fila,4,7,elimina_tildes(inscri.carrera), subtitulo3)
                        if matri=='':
                            grupoinsc=InscripcionGrupo.objects.filter(inscripcion=inscri)[:1].get()
                            ws.write_merge(com, fila,8,8,elimina_tildes(grupoinsc.grupo.nombre), subtitulo3)
                        else:
                            ws.write_merge(com, fila,8,8,elimina_tildes(matri.nivel.grupo.nombre), subtitulo3)
                        ws.write_merge(com, fila,9,9,elimina_tildes(inscri.fecha), subtitulo3)
                        ws.write_merge(com, fila,10,10,elimina_tildes(estado), subtitulo3)
                        ws.write_merge(com, fila,11,11,elimina_tildes(fecha_matricula), subtitulo3)

                        com=fila+1
                        fila = fila +1
                        columna=12

                    ws.write_merge(com, fila,0,3, "TOTALES:" ,titulo2)
                    ws.write_merge(com,fila,4,5,str(total_inscritos) +" Estudiantes",titulo2)
                    ws.write(fila,columna,total_inscripcion,titulo2)
                    ws.write(fila,columna+2,total_matricula,titulo2)
                    ws.write(fila,columna+4,total_cuota,titulo2)

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='valores_inscritos_general'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    nota='insrangofechas'
                    return HttpResponse(json.dumps({"result":str(ex)+" "+str(inscri)+" "+str(nota)}),content_type="application/json")
        else:
            data = {'title': 'Valores de Inscritos General'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=DistributivoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/xls_inscritos_porrangofecha.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

