from datetime import datetime
import json
import xlwt
import os
import locale
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT,UTILIZA_FACTURACION_CON_FPDF,JR_USEROUTPUT_FOLDER,MEDIA_URL, SITE_ROOT
from sga.commonviews import addUserData
from sga.forms import XLSPeriodoForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel,Periodo,Matricula
from sga.reportes import elimina_tildes
from fpdf import FPDF

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action  =='generarexcel':
                try:
                    periodo = Periodo.objects.filter(pk=request.POST['periodo'])[:1].get()
                    m = 10
                    #matriculados= Matricula.objects.filter(nivel__periodo=periodo,becado=True,inscripcion__id=52605).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                    matriculados= Matricula.objects.filter(nivel__periodo=periodo,becado=True).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, 'BECADOS POR PERIODO '+str(periodo),titulo2)

                    fila =4
                    detalle = 3
                    columna=0

                    beneficio=''
                    motivobeca=''
                    tipobeca=''
                    porcientobeca=''
                    nivel=''
                    paralelo=''
                    telefono2=''
                    correo1=''
                    correo2=''

                    ws.write(3,0,"IDENTIFICACION",subtitulo3)
                    ws.write(3,1,"ESTUDIANTE",subtitulo3)
                    ws.write(3,2,"NIVEL",subtitulo3)
                    ws.write(3,3,"PARALELO",subtitulo3)
                    ws.write(3,4,"TIPO DE BENEFICIO",subtitulo3)
                    ws.write(3,5,"PORCENTAJE DE BECA",subtitulo3)
                    ws.write(3,6,"MOTIVO DE BECA",subtitulo3)
                    ws.write(3,7,"TIPO DE BECA",subtitulo3)
                    ws.write(3,8,"EMAIL INSTITUCIONAL",subtitulo3)

                    for matri in matriculados:
                        print(matri)
                        if matri.inscripcion.persona.cedula:
                            identificacion=matri.inscripcion.persona.cedula
                        else:
                            identificacion=matri.inscripcion.persona.pasaporte

                        ws.write(fila,columna,str(identificacion), subtitulo)
                        ws.write(fila,columna+1,str(elimina_tildes(matri.inscripcion.persona.nombre_completo_inverso())), subtitulo)

                        if matri.nivel.nivelmalla:
                           nivel=matri.nivel.nivelmalla.nombrematriz
                        else:
                           nivel=''
                        ws.write(fila,columna+2,str(nivel), subtitulo)

                        if matri:
                           nivel=matri.nivel.paralelo
                        else:
                           nivel=''
                        ws.write(fila,columna+3,str(matri.nivel.paralelo), subtitulo)

                        if matri.tipobeneficio:
                           beneficio=matri.tipobeneficio
                        else:
                           beneficio=''
                        ws.write(fila,columna+4,str(beneficio), subtitulo)

                        if matri.porcientobeca:
                           porcientobeca=matri.porcientobeca
                        else:
                           porcientobeca=''
                        ws.write(fila,columna+5,str(porcientobeca), subtitulo)

                        if matri.motivobeca:
                           motivobeca=matri.motivobeca.nombrematriz
                        else:
                           motivobeca=''
                        ws.write(fila,columna+6,str(elimina_tildes(motivobeca)), subtitulo)

                        if matri.tipobeca:
                            tipobeca=matri.tipobeca
                        else:
                            tipobeca=''
                        ws.write(fila,columna+7,str(elimina_tildes(tipobeca)), subtitulo)

                        if matri.inscripcion.persona.emailinst:
                            correo2=matri.inscripcion.persona.emailinst
                        else:
                            correo2=''
                        ws.write(fila,columna+8,str(correo2), subtitulo)

                        fila = fila +1
                        columna=0

                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='becados_xperiodo'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(matri)}),content_type="application/json")

        else:
            data = {'title': 'Becados por Periodo'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                data['reportes'] = reportes
                data['generarform']=XLSPeriodoForm()
                return render(request ,"reportesexcel/becados_xperiodo.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


















