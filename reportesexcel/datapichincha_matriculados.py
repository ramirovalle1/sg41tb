from datetime import datetime,timedelta,date
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
from med.models import PersonaExtension
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import CacesRangoPeriodoForm
from sga.models import Periodo, convertir_fecha,ReporteExcel,Coordinacion,Matricula,\
    Inscripcion,PagoNivel
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):

    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                inscripcion= ''
                try:
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    center = xlwt.easyxf('align: horiz center')
                    ws = wb.add_sheet('Matriz',cell_overwrite_ok=True)
                    ws.write_merge(0, 0, 0, 30,)
                    ws.write_merge(1, 1, 0, 30,)
                    # ws.write (0, 0, 'INSTITUTO TECNOLOGICO BOLIVARIANO',center )
                    periodo=None
                    inicio=''
                    fin=''
                    if request.POST['periodo'] != '':
                        periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                        ws.write (1, 0, 'Periodo: ' + str(periodo.nombre),center )
                    else:
                        inicio = convertir_fecha( request.POST['inicio'])
                        fin = convertir_fecha(request.POST['fin'])
                        ws.write (1, 0, 'Desde: ' + str(inicio.date()) + " Hasta: " + str(fin.date()),center  )

                    ws.write(2, 0, 'TIPO DE ID', titulo)
                    ws.write(2, 1, 'IDENTIFICACION', titulo)
                    ws.write(2, 2, 'NACIONALIDAD', titulo)
                    ws.write(2, 3, 'PRIMER APELLIDO', titulo)
                    ws.write(2, 4, 'SEGUNDO APELLIDO', titulo)
                    ws.write(2, 5, 'NOMBRES', titulo)
                    ws.write(2, 6, 'FECHA DE NACIMIENTO', titulo)
                    ws.write(2, 7, 'SEXO', titulo)
                    ws.write(2, 8, 'ESTADO CIVIL', titulo)
                    ws.write(2, 9, 'PROVINCIA', titulo)
                    ws.write(2, 10, 'CIUDAD', titulo)
                    ws.write(2, 11, 'TELEFONO 1', titulo)
                    ws.write(2, 12, 'TELEFONO 2', titulo)
                    ws.write(2, 13, 'EMAIL PERSONAL', titulo)
                    ws.write(2, 14, 'CELULAR ', titulo)
                    ws.write(2, 15, 'TIPO DIRECCION ', titulo)
                    ws.write(2, 16, 'DIRECCION ', titulo)
                    ws.write(2, 17, 'FACULTAD ', titulo)
                    ws.write(2, 18, 'CARRERA', titulo)
                    ws.write(2, 19, 'EMAIL INSTITUCIONAL', titulo)
                    ws.write(2, 20, 'BECADO', titulo)
                    ws.write(2, 21, 'ESTADO', titulo)
                    ws.write(2, 22, 'EDAD', titulo)
                    ws.write(2, 23, 'SEMESTRE EN CURSO', titulo)
                    ws.write(2, 24, 'COSTO DE SEMESTRE', titulo)


                    cont = 3
                    c=1
                    if request.POST['periodo'] != '':
                        periodo= Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                        inscripid = Matricula.objects.filter(nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion')
                        # inscripid = Matricula.objects.filter(inscripcion__id=53680, becado=True,nivel__periodo=periodo,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion')
                    else:
                        print('fecha')
                        inicio = convertir_fecha( request.POST['inicio'])
                        fin = convertir_fecha(request.POST['fin'])
                        inscripid = Matricula.objects.filter(nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6,10),nivel__carrera__carrera=True).distinct('inscripcion').values('inscripcion')
                    for inscripcion in Inscripcion.objects.filter(id__in=inscripid):
                        # print(inscripcion)
                        anio = ''
                        tipoayuda=''
                        tipobeca=''
                        montorecibido=''
                        porcentaje=''
                        becado=''
                        telefono1=''
                        telefono2=''
                        correopersonal=''
                        correoinst=''
                        direccion=''
                        facultad=''
                        nivelmalla=''
                        matriculado=''
                        edad=''
                        matricula=''
                        costosemestre=0
                        if inscripcion.persona.pasaporte:
                            tipoDocumentoId = 'PASAPORTE'
                            try:
                                numeroIdentificacion = inscripcion.persona.pasaporte
                            except:
                                numeroIdentificacion= 'ERROR AL OBTENER PASAPORTE '
                        else:
                            tipoDocumentoId = 'CEDULA'
                            try:
                                numeroIdentificacion = inscripcion.persona.cedula
                            except:
                                numeroIdentificacion= 'ERROR AL OBTENER CEDULA '
                        if inscripcion.persona.sexo.nombre == "FEMENINO":
                            sexo = 'MUJER'
                        else:
                            sexo = 'HOMBRE'

                        if PersonaExtension.objects.filter(persona=inscripcion.persona).exists():
                            estadocivil=PersonaExtension.objects.filter(persona=inscripcion.persona)[:1].get()
                            edad = inscripcion.persona.edad_actual()
                            if estadocivil.estadocivil!=None:
                                estadocivil=elimina_tildes(estadocivil.estadocivil.nombre)
                            else:
                                estadocivil=''
                        else:
                            estadocivil=''
                            edad=''

                        if periodo:
                            matricula = Matricula.objects.filter(inscripcion=inscripcion,nivel__periodo=periodo)[:1].get()
                        else:
                            if Matricula.objects.filter(inscripcion=inscripcion,nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True).exists():
                                matricula=Matricula.objects.filter(inscripcion=inscripcion,nivel__periodo__inicio__gte=inicio,nivel__periodo__inicio__lte=fin,nivel__nivelmalla__in=(1,2,3,4,5,6),nivel__carrera__carrera=True)[:1].get()
                        if matricula:
                            if PagoNivel.objects.filter(nivel=matricula.nivel).exists():
                                costosemestre=PagoNivel.objects.filter(nivel=matricula.nivel).aggregate(Sum('valor'))['valor__sum']
                            else:
                                costosemestre=0
                            if matricula.becado:
                                becado='SI'
                            else:
                                becado='NO'
                            if matricula.nivel.nivelmalla:
                                nivelmalla=elimina_tildes(matricula.nivel.nivelmalla.nombre)
                                if matricula.nivel.nivelmalla.id==10:
                                    matriculado=nivelmalla
                                else:
                                    matriculado='MATRICULADO'
                            else:
                                matriculado='MATRICULADO'
                                nivelmalla=''
                        else:
                            costosemestre=0
                            becado=''
                            matriculado=''
                            nivelmalla=''
                        try:
                            nombres = elimina_tildes(inscripcion.persona.nombres)
                        except:
                            nombres ='ERROR EN NOMBRE'
                        try:
                            apellido1 = elimina_tildes(inscripcion.persona.apellido1)
                        except:
                            apellido1 ='ERROR EN APELLIDO1'
                        try:
                            apellido2 = elimina_tildes(inscripcion.persona.apellido2)
                        except:
                            apellido2 ='ERROR EN APELLIDO2'
                        try:
                            if inscripcion.persona.telefono_conv:
                                telefono1=inscripcion.persona.telefono_conv.replace("-","")
                            else:
                                telefono1=''
                        except Exception as ex:
                            pass
                        try:
                            if inscripcion.persona.telefono:
                                telefono2=inscripcion.persona.telefono.replace("-","")
                            else:
                                telefono2=''
                        except Exception as ex:
                            pass
                        try:
                            if inscripcion.persona.emailinst:
                                correoinst=inscripcion.persona.emailinst
                            else:
                                correoinst=''
                        except Exception as ex:
                            pass
                        try:
                            if inscripcion.persona.email:
                                correopersonal=inscripcion.persona.email
                            else:
                                correopersonal=''
                        except Exception as ex:
                            pass

                        if inscripcion.carrera:
                            carrera=elimina_tildes(inscripcion.carrera.nombre)
                            facultad=Coordinacion.objects.filter(carrera=inscripcion.carrera)[:1].get()
                        else:
                            carrera=''
                            facultad=''
                        if inscripcion.persona.nacionalidad:
                            nacionalidad=elimina_tildes(inscripcion.persona.nacionalidad.nombre)
                        else:
                            nacionalidad=''
                        if inscripcion.persona.nacimiento:
                            fnacimiento=elimina_tildes(inscripcion.persona.nacimiento)
                        else:
                            fnacimiento=''
                        if inscripcion.persona.provinciaresid:
                            provincia=elimina_tildes(inscripcion.persona.provinciaresid.nombre)
                        else:
                            provincia=''
                        if inscripcion.persona.cantonresid:
                            ciudad=elimina_tildes(inscripcion.persona.cantonresid.nombre)
                        else:
                            ciudad=''
                        try:
                            direccion = elimina_tildes(inscripcion.persona.direccion)
                        except:
                            direccion= ''

                        ws.write(cont, 0, tipoDocumentoId)
                        ws.write(cont, 1, numeroIdentificacion)
                        ws.write(cont, 2, nacionalidad)
                        ws.write(cont, 3, apellido1)
                        ws.write(cont, 4, apellido2)
                        ws.write(cont, 5, nombres)
                        ws.write(cont, 6, fnacimiento)
                        ws.write(cont, 7, sexo)
                        ws.write(cont, 8, estadocivil)
                        ws.write(cont, 9, provincia)
                        ws.write(cont, 10,ciudad)
                        ws.write(cont, 11,telefono1)
                        ws.write(cont, 12,'')
                        ws.write(cont, 13,correopersonal)
                        ws.write(cont, 14,telefono2)
                        ws.write(cont, 15,'DOMICILIO')
                        ws.write(cont, 16,direccion)
                        ws.write(cont, 17,elimina_tildes(facultad.nombre))
                        ws.write(cont, 18,carrera)
                        ws.write(cont, 19,correoinst)
                        ws.write(cont, 20,becado)
                        ws.write(cont, 21,matriculado)
                        ws.write(cont, 22,str(edad))
                        ws.write(cont, 23,nivelmalla)
                        ws.write(cont, 24,costosemestre)
                        cont=cont+1
                        # print(cont)

                    nombre ='data_alumnos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print((ex))
                    return HttpResponse(json.dumps({"result":str(ex)+str(inscripcion)}),content_type="application/json")
        else:
                data = {'title': 'Data de Matriculados'}
                addUserData(request,data)
                if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                    reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                    data['reportes'] = reportes
                    data['generarform']= CacesRangoPeriodoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                    return render(request ,"reportesexcel/datapichincha.html" ,  data)
                return HttpResponseRedirect("/reporteexcel")


    except Exception as e:
        print((e))
        return HttpResponseRedirect('/?info='+str(e))