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
from sga.forms import RangoFacturasForm,RangoNCForm, VinculacionExcelForm, GestionExcelForm
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, \
     Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, \
     Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, RubroMatricula, Pago, RubroCuota,Provincia,Parroquia,Canton,Sector

from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    nivel = Nivel.objects.filter(pk=request.POST['nivel'])[:1].get()
                    m = 10
                    total=nivel.matriculados().count()
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
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
                    ws.write_merge(1, 1,0,m, 'MATRICULADOS SMS',titulo2)
                    ws.write(3, 0,'CARRERA: ' +elimina_tildes(nivel.carrera.nombre)  , subtitulo)
                    ws.write(4, 0,'GRUPO:   ' +elimina_tildes(nivel.grupo.nombre) , subtitulo)
                    ws.write(5, 0,'NIVEL:   ' +elimina_tildes(nivel.nivelmalla.nombre) , subtitulo)
                    ws.write(6,0,"IDENTIFICACION",subtitulo3)
                    ws.write_merge(6, 6,1,3,"ESTUDIANTE",subtitulo3)
                    ws.write(6,4,"CELULAR",subtitulo3)
                    # OC 14-06-2018 se agregan los correos que tengan registrados los estudiantes
                    ws.write(6,5,"EMAIL INST",subtitulo3)
                    ws.write(6,6,"EMAIL 1",subtitulo3)
                    ws.write(6,7,"EMAIL 2",subtitulo3)
                    ws.write(6,8,"EMAIL 3",subtitulo3)
                    ws.write(6,9,"USUARIO INSCRIPCION",subtitulo3)
                    ws.write(6,10,"CONVENCIONAL",subtitulo3)
                    ws.write(6,11,"FECHA INSCRIPCION",subtitulo3)
                    ws.write(6,12,"EDAD DEL ESTUDIANTE",subtitulo3)
                    #OCastillo 19-10-2021 se agregan nuevas columnas segun requerimiento
                    ws.write(6,13,"PROVINCIA RESIDENCIA",subtitulo3)
                    ws.write(6,14,"CANTON RESIDENCIA",subtitulo3)
                    ws.write(6,15,"PARROQUIA",subtitulo3)
                    ws.write(6,16,"SECTOR",subtitulo3)

                    fila = 7
                    com = 7
                    detalle = 3
                    columna=3
                    matri=''
                    identificacion=''

                    #para pruebas
                    # matricula= Matricula.objects.filter(inscripcion__id=95280,nivel=nivel)
                    # for matri in matricula:

                    for matri in nivel.matriculados():
                        print(matri)
                        celular=''
                        correo1=''
                        correo2=''
                        correo3=''
                        correo4=''
                        convencional=''
                        provincia_residencia=''
                        canton_residencia=''
                        parroquia=''
                        sector_residencia=''
                        try:
                            if matri.inscripcion.persona.telefono:
                                celular=str(matri.inscripcion.persona.telefono)
                        except Exception as t:
                                celular=''

                        try:
                            if matri.inscripcion.persona.telefono_conv:
                                convencional=str(matri.inscripcion.persona.telefono_conv)
                        except Exception as t:
                            convencional=''

                        try:
                            if matri.inscripcion.persona.emailinst:
                                correo1=str(matri.inscripcion.persona.emailinst)
                            else:
                                correo1=''
                        except Exception as t:
                            correo1=''

                        try:
                            if matri.inscripcion.persona.email:
                                correo2=str(matri.inscripcion.persona.email)
                            else:
                                correo2=''
                        except Exception as t:
                            correo2=''

                        try:
                            if matri.inscripcion.persona.email1:
                                correo3=str(matri.inscripcion.persona.email1)
                            else:
                                correo3=''
                        except Exception as t:
                            correo3=''

                        try:
                            if matri.inscripcion.persona.email2:
                                correo4=matri.inscripcion.persona.email2
                            else:
                                correo4=''
                        except Exception as t:
                            correo4=''

                        if matri.inscripcion.persona.cedula:
                            identificacion=matri.inscripcion.persona.cedula
                        else:
                            identificacion=elimina_tildes(matri.inscripcion.persona.pasaporte)

                        if matri.inscripcion.fecha:
                            fecha_ins=matri.inscripcion.fecha
                        else:
                            fecha_ins=''

                        if matri.inscripcion.persona.nacimiento:
                            edad=matri.inscripcion.persona.edad_actual()
                        else:
                            edad=''

                        if matri.inscripcion.persona.provinciaresid:
                            provincia_residencia= Provincia.objects.get(id=matri.inscripcion.persona.provinciaresid.id)
                        else:
                            provincia_residencia=''

                        if matri.inscripcion.persona.cantonresid:
                            canton_residencia= Canton.objects.get(id=matri.inscripcion.persona.cantonresid.id)
                        else:
                            canton_residencia=''

                        if matri.inscripcion.persona.parroquia_id:
                            parroquia= Parroquia.objects.get(id=matri.inscripcion.persona.parroquia.id)
                        else:
                            parroquia=''

                        try:
                            if matri.inscripcion.persona.sectorresid:
                                sector_residencia=Sector.objects.get(id=matri.inscripcion.persona.sectorresid.id)
                            else:
                                sector_residencia=''
                        except Exception as ex:
                            pass


                        ws.write(fila,0,identificacion,subtitulo3)
                        ws.write_merge(com, fila,1,3,elimina_tildes(matri.inscripcion.persona.nombre_completo_inverso()), subtitulo)
                        ws.write(fila,columna+1,str(celular),subtitulo3)
                        ws.write(fila,columna+2,str(correo1),subtitulo3)
                        ws.write(fila,columna+3,str(correo2),subtitulo3)
                        ws.write(fila,columna+4,str(correo3),subtitulo3)
                        ws.write(fila,columna+5,str(correo4),subtitulo3)
                        ws.write(fila,columna+6,str(matri.inscripcion.user),subtitulo3)
                        ws.write(fila,columna+7,str(convencional),subtitulo3)
                        ws.write(fila,columna+8,str(fecha_ins),subtitulo3)
                        ws.write(fila,columna+9,str(edad),subtitulo3)
                        ws.write(fila,columna+10,elimina_tildes(provincia_residencia),subtitulo3)
                        ws.write(fila,columna+11,elimina_tildes(canton_residencia),subtitulo3)
                        ws.write(fila,columna+12,elimina_tildes(parroquia),subtitulo3)
                        ws.write(fila,columna+13,elimina_tildes(sector_residencia),subtitulo3)

                        com=fila+1
                        fila=fila+1

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='matriculados_sms'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)+' '+ str(matri)}),content_type="application/json")

        else:
            data = {'title': 'Matriculados SMS'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/matriculados_sms.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        print(e)
        return HttpResponseRedirect('/?info='+str(e))

