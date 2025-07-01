from datetime import datetime,timedelta
import json
import xlrd
import xlwt
import psycopg2
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
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, GestionExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, RubroMatricula, Pago, RubroCuota

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']

            if action :
                wb = xlwt.Workbook()
                ws = wb.add_sheet('Registros',cell_overwrite_ok=True)
                try:
                    m = 10
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, 'BASE DE MATRICULADOS',titulo2)

                    ws.write(3,0,"No. Cedula",subtitulo3)
                    ws.write(3,1,"Email",subtitulo3)
                    ws.write(3,2,"Password",subtitulo3)
                    ws.write(3,3,"Nombres y Apellidos",subtitulo3)
                    ws.write(3,4,"Nombres",subtitulo3)
                    ws.write(3,5,"Apellidos",subtitulo3)
                    ws.write(3,6,"Institucion",subtitulo3)
                    ws.write(3,7,"Telefono",subtitulo3)
                    ws.write(3,8,"Facebook url",subtitulo3)
                    ws.write(3,9,"Twitter url",subtitulo3)
                    ws.write(3,10,"Instagram url",subtitulo3)
                    ws.write(3,11,"TikTok",subtitulo3)

                    fila = 4
                    detalle = 3
                    matri=''
                    identificacion=''
                    institucion="INSTITUTO SUPERIOR TECNOLOGICO BOLIVARIANO DE TECNOLOGIA"
                    redsocial1="https://www.facebook.com/itb.edu.ec"
                    redsocial2="https://twitter.com/itbolivariano"
                    redsocial3="https://www.instagram.com/itb_ec/"

                    cn = psycopg2.connect("host=10.10.9.45 dbname=aok user=aok password=R0b3rt0.1tb$") #DATOS DE LA BASE
                    #cn = psycopg2.connect("host=localhost dbname=academico_31marzo user=postgres password=sa") #DATOS DE LA BASE LOCAL
                    cur = cn.cursor()
                    cur.execute("select * from matriculados ")
                    matriculados = cur.fetchall()

                    #for matri in Matricula.objects.filter(nivel__cerrado=False,nivel__carrera__carrera=True,liberada=False,inscripcion__persona__usuario__is_active=True,nivel__periodo__activo=True).exclude(nivel__nivelmalla__id=10).distinct('inscripcion'):
                    for matri in matriculados:
                        try:
                            celular=''
                            identificacion=''
                            correo=''
                            nombres=''
                            apellidos=''
                            nombrecompleto= ''

                            if matri[4]:
                                #identificacion = matri.inscripcion.persona.cedula
                                identificacion = matri[4]
                            else:
                                #identificacion = matri.inscripcion.persona.pasaporte
                                identificacion = matri[5]

                            try:
                                #nombrecompleto=elimina_tildes(matri.inscripcion.persona.nombre_completo())
                                nombrecompleto=str(elimina_tildes(matri[3])+' '+elimina_tildes(matri[1])+' '+elimina_tildes(matri[2]))
                            except :
                                nombrecompleto=''

                            try:
                                #nombres = elimina_tildes(matri.inscripcion.persona.nombres)
                                nombres = str(elimina_tildes(matri[3]))
                            except:
                                nombres = ''

                            try:
                                #apellidos = elimina_tildes(matri.inscripcion.persona.apellido1)+' '+elimina_tildes(matri.inscripcion.persona.apellido2)
                                apellidos = str(elimina_tildes(matri[1])+' '+elimina_tildes(matri[2]))
                            except:
                                apellidos = ''

                            try:
                                if matri[6]:
                                    #correo= elimina_tildes(matri.inscripcion.persona.emailinst)
                                    correo= elimina_tildes(matri[6])
                            except:
                                correo=''

                            try:
                                if matri[7]:
                                    celular=elimina_tildes(matri[7])
                            except :
                                celular=''

                            ws.write(fila,0,str(identificacion),subtitulo3)
                            ws.write(fila,1,str(correo),subtitulo3)
                            ws.write(fila,2,str(identificacion),subtitulo3)
                            ws.write(fila,3,str(nombrecompleto),subtitulo3)
                            ws.write(fila,4,str(nombres),subtitulo3)
                            ws.write(fila,5,str(apellidos),subtitulo3)
                            ws.write(fila,6,str(institucion),subtitulo3)
                            ws.write(fila,7,str(celular),subtitulo3)
                            ws.write(fila,8,str(redsocial1),subtitulo3)
                            ws.write(fila,9,str(redsocial2),subtitulo3)
                            ws.write(fila,10,str(redsocial3),subtitulo3)
                            ws.write(fila,11,"",subtitulo3)

                            fila=fila+1
                            #print(fila)
                        except:
                            print((identificacion))
                            pass

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(fila+5,0, "Usuario", subtitulo)
                    ws.write(fila+5,1, str(request.user), subtitulo)

                except Exception as ex:
                    print(str(ex))
                    pass
                nombre ='base_matriculados'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

        else:
            data = {'title': 'Base de Matriculados'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/base_matriculados.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

