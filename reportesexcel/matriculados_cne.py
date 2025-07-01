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
from sga.models import Inscripcion,convertir_fecha,Factura,ClienteFactura,TituloInstitucion,ReporteExcel,NotaCreditoInstitucion, Persona,TipoNotaCredito, Carrera, Matricula, RecordAcademico, Egresado, Malla, AsignaturaMalla, NivelMalla, MateriaAsignada, Asignatura, Nivel, Periodo, ProfesorMateria, PagoNivel, Rubro, RubroMatricula, Pago, RubroCuota, SesionJornada

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
                    ws.write_merge(1, 1,0,m, 'MATRICULADOS CNE',titulo2)

                    ws.write(3,1,"TIPO",subtitulo3)
                    ws.write(3,2,"CEDULA",subtitulo3)
                    ws.write(3,3,"NOMBRES Y APELLIDOS",subtitulo3)
                    ws.write(3,4,"INSTRUCCION",subtitulo3)
                    ws.write(3,5,"DIRECCION 1 ",subtitulo3)
                    ws.write(3,6,"NUMERO",subtitulo3)
                    ws.write(3,7,"DIRECCION 2",subtitulo3)
                    ws.write(3,8,"REFERENCIA",subtitulo3)
                    ws.write(3,9,"CANTON",subtitulo3)
                    # OC 14-06-2018 se agregan los correos que tengan registrados los estudiantes
                    ws.write(3,10,"PARROQUIA",subtitulo3)
                    ws.write(3,11,"BARRIO",subtitulo3)
                    ws.write(3,12,"SECTOR",subtitulo3)
                    ws.write(3,13,"CONVENCIONAL",subtitulo3)
                    ws.write(3,14,"CELULAR",subtitulo3)
                    ws.write(3,15,"CORREO",subtitulo3)
                    ws.write(3,16,"CORREO INS",subtitulo3)
                    ws.write(3,17,"AREA O DPTO",subtitulo3)
                    ws.write(3,18,"MODALIDAD",subtitulo3)
                    ws.write(3,19,"FACULTAD",subtitulo3)
                    ws.write(3,20,"PARALELO",subtitulo3)
                    ws.write(3,21,"JORNADA",subtitulo3)

                    fila = 4

                    matri=''

                    inscrip=Matricula.objects.filter(nivel__cerrado=False,nivel__carrera__carrera=True).exclude(liberada=True).values('inscripcion').distinct('inscripcion')
                    for inscripcion in Inscripcion.objects.filter(id__in=inscrip).order_by('persona__apellido1','persona__apellido2'):
                        matri = inscripcion.matricula()

                        try:
                            celular=''
                            correo1=''
                            correo2=''
                            correo3=''
                            correo4=''

                            if matri.inscripcion.persona.cedula:
                                iden='CED'
                                cedula = matri.inscripcion.persona.cedula
                            else:
                                iden='PAS'
                                cedula = matri.inscripcion.persona.pasaporte

                            direccion = ''
                            try:
                                if matri.inscripcion.persona.direccion:
                                    direccion =elimina_tildes(matri.inscripcion.persona.direccion)
                            except:
                                direccion = ''


                            nombrecompleto= ''
                            try:
                                nombrecompleto=elimina_tildes(matri.inscripcion.persona.nombre_completo())
                            except :
                                nombrecompleto=''

                            direccion2 = ''
                            try:
                                if matri.inscripcion.persona.direccion2:
                                    direccion2 = elimina_tildes(matri.inscripcion.persona.direccion2)
                            except:
                                direccion2 = ''

                            numcasa = ''
                            try:
                                if matri.inscripcion.persona.num_direccion:
                                    numcasa = elimina_tildes(matri.inscripcion.persona.num_direccion)
                            except:
                                numcasa = ''


                            referencia = ''
                            canton=''
                            if matri.inscripcion.persona.cantonresid:
                                try:
                                    canton = elimina_tildes(matri.inscripcion.persona.cantonresid.nombre)
                                except :
                                    canton = ''

                            parro=''
                            if matri.inscripcion.persona.parroquia:
                                try:
                                    parro = elimina_tildes(matri.inscripcion.persona.parroquia.nombre)
                                except :
                                    parro = ''

                            barrio = ''

                            sector = ''
                            if matri.inscripcion.persona.sectorresid:
                                try:
                                    sector = elimina_tildes(matri.inscripcion.persona.sectorresid.nombre)
                                except:
                                    sector = ''

                            convencional=''
                            try:
                                if matri.inscripcion.persona.telefono_conv:
                                    convencional=elimina_tildes(matri.inscripcion.persona.telefono_conv)
                            except Exception as t:
                                    convencional=''

                            try:
                                if matri.inscripcion.persona.telefono:
                                    celular=elimina_tildes(matri.inscripcion.persona.telefono)
                            except Exception as t:
                                    celular=''

                            if matri.inscripcion.persona.emailinst:
                                correo1= elimina_tildes(matri.inscripcion.persona.emailinst)
                            else:
                                correo1=''

                            if matri.inscripcion.persona.email:
                                correo2=elimina_tildes(matri.inscripcion.persona.email)
                            else:
                                correo2=''

                            try:
                                carrera = elimina_tildes(matri.inscripcion.carrera.nombre)
                            except:
                                carrera = ''

                            if matri.inscripcion.modalidad:
                                modalidad=matri.inscripcion.modalidad.nombre
                            else:
                                modalidad=''

                            if matri.inscripcion.carrera.coordinacion_pertenece():
                                facultad =matri.inscripcion.carrera.coordinacion_pertenece().nombre
                            else:
                                facultad =''

                            if matri.nivel.paralelo:
                                paralelo =matri.nivel.paralelo
                            else:
                                paralelo =''
                            if SesionJornada.objects.filter(sesion=matri.nivel.sesion).exists():
                                jornada = SesionJornada.objects.filter(sesion=matri.nivel.sesion)[:1].get().jornada.nombre
                            else:
                                jornada  =''

                            ws.write(fila,1,(iden),subtitulo3)
                            ws.write(fila,2,str(cedula),subtitulo3)
                            ws.write(fila,3,(nombrecompleto),subtitulo3)
                            ws.write(fila,4,"Bachiller",subtitulo3)
                            ws.write(fila,5,str(direccion),subtitulo3)
                            ws.write(fila,6,str(numcasa),subtitulo3)
                            ws.write(fila,7,str(direccion2),subtitulo3)
                            ws.write(fila,8,str(referencia),subtitulo3)
                            ws.write(fila,9,str(canton),subtitulo3)
                            ws.write(fila,10,str(parro),subtitulo3)
                            ws.write(fila,11,barrio,subtitulo3)
                            ws.write(fila,12,sector,subtitulo3)
                            ws.write(fila,13,convencional,subtitulo3)
                            ws.write(fila,14,celular,subtitulo3)
                            ws.write(fila,15,correo2,subtitulo3)
                            ws.write(fila,16,correo1,subtitulo3)
                            ws.write(fila,17,carrera,subtitulo3)
                            ws.write(fila,18,modalidad,subtitulo3)
                            ws.write(fila,19,facultad,subtitulo3)
                            ws.write(fila,20,paralelo,subtitulo3)
                            ws.write(fila,21,jornada,subtitulo3)
                            com=fila+1
                            fila=fila+1
                        except:
                            print((cedula))
                            pass

                    # detalle = detalle + fila
                    # ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    # ws.write(detalle,1, str(datetime.now()), subtitulo)
                    # detalle=detalle+2
                    ws.write(fila+5,0, "Usuario", subtitulo)
                    ws.write(fila+6,1, str(request.user), subtitulo)

                except Exception as ex:
                    print(str(ex))
                    pass
                nombre ='matriculados_cne'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

        else:
            data = {'title': 'Matriculados SMS'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                return render(request ,"reportesexcel/matriculados_cne.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

