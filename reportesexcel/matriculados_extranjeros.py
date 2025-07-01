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
from settings import UTILIZA_GRUPOS_ALUMNOS, EMAIL_ACTIVE,MEDIA_ROOT, SITE_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import MatriculadosporCarreraExcelForm, RangoFacturasForm
from sga.models import Inscripcion,convertir_fecha,TituloInstitucion,ReporteExcel,Carrera,Matricula,Colegio,Canton,EmpresaInscripcion
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    m = 8
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    inicio = request.POST['inicio']
                    fin = request.POST['fin']

                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Informacion',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'MATRICULADOS EXTRANJEROS', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)

                    ws.write(6, 0,  'IDENTIFICACION', titulo)
                    ws.write(6, 1,  'ESTUDIANTE', titulo)
                    ws.write(6, 2,  'NIVEL', titulo)
                    ws.write(6, 3,  'MODALIDAD', titulo)
                    ws.write(6, 4,  'PARALELO', titulo)
                    ws.write(6, 5,  'CONVENCIONAL', titulo)
                    ws.write(6, 6,  'CELULAR', titulo)
                    ws.write(6, 7,  'Email Institucional', titulo)
                    ws.write(6, 8,  'Email Personal', titulo)
                    ws.write(6, 9,  'Nacionalidad', titulo)

                    # ws.write(6, 9,  'CIUDAD RESIDENCIA', titulo)
                    # ws.write(6, 10,  'SECTOR', titulo)
                    # ws.write(6, 11,  'COLEGIO', titulo)
                    # ws.write(6, 12,  'EMPRESA', titulo)
                    # ws.write(6, 13,  'CARGO', titulo)

                    matriculados = Matricula.objects.filter(inscripcion__persona__usuario__is_active=True,fecha__gte=fechai,fecha__lte=fechaf,inscripcion__persona__extranjero=True).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    # matriculados = Matricula.objects.filter(inscripcion__id=48642,nivel__carrera=carrera).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    detalle = 4
                    fila = 7

                    identificacion=''
                    estudiante=''
                    ciudad_residencia=''
                    colegio=''
                    sector=''
                    empresa=''
                    nombreempresa=''
                    cargo=''
                    matri=''
                    nivel=''
                    paralelo=''
                    emailinst=''
                    email=''
                    telefono=''
                    celular=''
                    modalidad=''
                    nacionalidad=''

                    for matri in matriculados:
                        if not matri.absentismo() and not matri.esta_retirado():
                            print((matri))
                            if matri.inscripcion.persona.cedula:
                                identificacion=matri.inscripcion.persona.cedula
                            else:
                                identificacion=matri.inscripcion.persona.pasaporte

                            estudiante=matri.inscripcion.persona.nombre_completo_inverso()
                            nivel=matri.nivel.nivelmalla.nombre
                            paralelo=matri.nivel.grupo.nombre
                            modalidad=matri.inscripcion.modalidad.nombre

                            if matri.inscripcion.estcolegio_id:
                                colegio= Colegio.objects.get(id=matri.inscripcion.estcolegio_id)
                            else:
                                colegio=''

                            if matri.inscripcion.persona.cantonresid:
                                ciudad_residencia= Canton.objects.get(id=matri.inscripcion.persona.cantonresid.id)
                            else:
                                ciudad_residencia=''

                            try:
                                if matri.inscripcion.persona.sector:
                                    sector=elimina_tildes(matri.inscripcion.persona.sector)
                                else:
                                    sector=''
                            except Exception as ex:
                                pass

                            if EmpresaInscripcion.objects.filter(inscripcion=matri.inscripcion).exists():
                                empresa=EmpresaInscripcion.objects.get(inscripcion=matri.inscripcion)
                                nombreempresa=empresa.razon
                                cargo=empresa.cargo
                            else:
                                nombreempresa=''
                                cargo=''

                            try:
                                if matri.inscripcion.persona.telefono_conv:
                                    telefono=matri.inscripcion.persona.telefono_conv.replace("-","")
                                else:
                                    telefono=''
                            except Exception as ex:
                                pass

                            try:
                                if matri.inscripcion.persona.telefono:
                                    celular=matri.inscripcion.persona.telefono.replace("-","")
                                else:
                                    celular=''
                            except Exception as ex:
                                pass

                            if matri.inscripcion.persona.emailinst:
                                emailinst=matri.inscripcion.persona.emailinst
                            else:
                                emailinst=''

                            if matri.inscripcion.persona.email:
                                email=matri.inscripcion.persona.email
                            else:
                                email=''
                            try:
                                if matri.inscripcion.persona.nacionalidad:
                                    nacionalidad=elimina_tildes(matri.inscripcion.persona.nacionalidad.nombre)
                                else:
                                    nacionalidad=''
                            except Exception as ex:
                                pass


                            ws.write(fila,0, str(identificacion))
                            ws.write(fila,1, elimina_tildes(estudiante))
                            ws.write(fila,2, nivel)
                            ws.write(fila,3,elimina_tildes(modalidad))
                            ws.write(fila,4, paralelo)
                            ws.write(fila,5, telefono)
                            ws.write(fila,6, celular)
                            ws.write(fila,7, emailinst)
                            ws.write(fila,8, email)
                            ws.write(fila,9, nacionalidad)
                            # ws.write(fila,9, elimina_tildes(ciudad_residencia))
                            # ws.write(fila,10, sector)
                            # ws.write(fila,11, elimina_tildes(colegio))
                            # ws.write(fila,12, elimina_tildes(nombreempresa))
                            # ws.write(fila,13, elimina_tildes(cargo))

                            fila=fila + 1

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='matriculados_extranjeros'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(matri)}),content_type="application/json")

        else:
            data = {'title': 'Matriculados Extranjeros'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
            return render(request ,"reportesexcel/matriculados_extranjeros.html" ,  data)

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

