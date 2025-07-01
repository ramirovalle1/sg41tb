from datetime import datetime, timedelta
import json
import xlwt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm
from sga.models import convertir_fecha,TituloInstitucion, PagoPymentez, Rubro, Carrera, SeguimientoGraduado, Graduado, Persona
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                try:
                    inicio = request.POST['inicio']
                    fin = request.POST['fin']
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)+timedelta(hours=23,minutes=59)
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Listado',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,14, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,14, 'SEGUIMIENTO A GRADUADOS POR RANGO DE FECHAS', titulo2)
                    ws.write(2, 0, 'DESDE', titulo)
                    ws.write(2, 1, str((fechai.date())), titulo)
                    ws.write(3, 0, 'HASTA:', titulo)
                    ws.write(3, 1, str((fechaf.date())), titulo)
                    fila=5

                    seguimiento = SeguimientoGraduado.objects.filter(fecha__gte=fechai, fecha__lte=fechaf).order_by('fecha','graduado__inscripcion__carrera' ,'graduado__inscripcion__persona__apellido1','graduado__inscripcion__persona__apellido2','graduado__inscripcion__persona__nombres')
                    if seguimiento.exists():
                        ws.write(fila, 0,  'FECHA', titulo)
                        ws.write(fila, 1, 'HORA',titulo)
                        ws.write(fila, 2,  'RESPONSABLE', titulo)
                        ws.write(fila, 3,  'CARRERA', titulo)
                        ws.write(fila, 4,  'IDENTIFICACION', titulo)
                        ws.write(fila, 5,  'NOMBRES', titulo)
                        ws.write(fila, 6,  'F. GRADUADO', titulo)
                        ws.write(fila, 7,  'EMAIL PERSONAL', titulo)
                        ws.write(fila, 8,  'EMAIL 2', titulo)
                        ws.write(fila, 9,  'CELULAR', titulo)
                        ws.write(fila, 10, 'TELEFONO CONV.', titulo)
                        ws.write(fila, 11, 'EMPRESA', titulo)
                        ws.write(fila, 12, 'CARGO', titulo)
                        ws.write(fila, 13, 'OCUPACION', titulo)
                        ws.write(fila, 14, 'TELEFONO TRABAJO', titulo)
                        ws.write(fila, 15, 'EMAIL TRABAJO',titulo)
                        ws.write(fila, 16, 'SUELDO',titulo)
                        ws.write(fila, 17, 'EJERCE PROFESION',titulo)
                        ws.write(fila, 18, 'OBSERVACIONES',titulo)
                        ws.write(fila, 19, 'PROVINCIA NACIMIENTO',titulo)
                        ws.write(fila, 20, 'CANTON NACIMIENTO',titulo)
                        ws.write(fila, 21, 'PROVINCIA RESIDENCIA',titulo)
                        ws.write(fila, 22, 'CANTON RESIDENCIA',titulo)

                        for sg in seguimiento:
                            fila=fila+1
                            try:
                                ws.write(fila, 0, str(sg.fecha))
                            except:
                                ws.write(fila, 0, '')
                            try:
                                formato = '%H:%M:%S'
                                hora = sg.hora.strftime(formato)
                                ws.write(fila, 1, str(hora))
                            except:
                                ws.write(fila, 1, '')
                            try:
                                persona = Persona.objects.filter(usuario=sg.usuario)[:1].get()
                                ws.write(fila, 2, elimina_tildes(persona.nombre_completo_inverso()))
                            except:
                                ws.write(fila, 2, '')
                            try:
                                ws.write(fila, 3, elimina_tildes(sg.graduado.inscripcion.carrera.nombre))
                            except:
                                ws.write(fila, 3, '')
                            try:
                                ws.write(fila, 4, elimina_tildes(sg.graduado.inscripcion.persona.cedula))
                            except:
                                ws.write(fila, 4, '')
                            try:
                                ws.write(fila, 5, elimina_tildes(sg.graduado.inscripcion.persona.nombre_completo_inverso()))
                            except:
                                ws.write(fila, 5, '')
                            try:
                                ws.write(fila, 6, elimina_tildes(sg.graduado.fechagraduado))
                            except:
                                ws.write(fila, 6, '')
                            try:
                                ws.write(fila, 7, elimina_tildes(sg.graduado.inscripcion.persona.email))
                            except:
                                ws.write(fila, 7, '')
                            try:
                                ws.write(fila, 8, elimina_tildes(sg.graduado.inscripcion.persona.email1))
                            except:
                                ws.write(fila, 8, '')
                            try:
                                ws.write(fila, 9, elimina_tildes(sg.graduado.inscripcion.persona.telefono))
                            except:
                                ws.write(fila, 9, '')
                            try:
                                ws.write(fila, 10, elimina_tildes(sg.graduado.inscripcion.persona.telefono_conv))
                            except:
                                ws.write(fila, 10, '')
                            try:
                                ws.write(fila, 11, elimina_tildes(sg.empresa))
                            except:
                                ws.write(fila, 11, '')
                            try:
                                ws.write(fila, 12, elimina_tildes(sg.cargo))
                            except:
                                ws.write(fila, 12, '')
                            try:
                                ws.write(fila, 13, elimina_tildes(sg.ocupacion))
                            except:
                                ws.write(fila, 13, '')
                            try:
                                ws.write(fila, 14, elimina_tildes(sg.telefono))
                            except:
                                ws.write(fila, 14, '')
                            try:
                                ws.write(fila, 15, elimina_tildes(sg.email))
                            except:
                                ws.write(fila, 15, '')
                            try:
                                if sg.sueldo:
                                    ws.write(fila, 16, elimina_tildes(sg.sueldo))
                                else:
                                    ws.write(fila, 16, '')
                            except:
                                ws.write(fila, 16, '')
                            try:
                                if sg.ejerce==True:
                                    ejerce = 'SI'
                                else:
                                    ejerce = 'NO'
                                ws.write(fila, 17, ejerce)
                            except:
                                ws.write(fila, 17, '')
                            try:
                                ws.write(fila, 18, elimina_tildes(sg.observaciones))
                            except:
                                ws.write(fila, 18, '')
                            try:
                                ws.write(fila, 19, elimina_tildes(sg.graduado.inscripcion.persona.provincia))
                            except:
                                ws.write(fila, 19, '')
                            try:
                                ws.write(fila, 20, elimina_tildes(sg.graduado.inscripcion.persona.canton))
                            except:
                                ws.write(fila, 20, '')
                            try:
                                ws.write(fila, 21, elimina_tildes(sg.graduado.inscripcion.persona.provinciaresid))
                            except:
                                ws.write(fila, 21, '')
                            try:
                                ws.write(fila, 22, elimina_tildes(sg.graduado.inscripcion.persona.cantonresid))
                            except:
                                ws.write(fila, 22, '')

                        fila=fila+3


                    nombre ='Seguimiento_Graduados'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(ex)
                    # return HttpResponse(json.dumps({"result":str(ex) + " "+  str(p.inscripcion)}),content_type="application/json")
        else:
            data = {'title': 'Seguimiento Graduados'}
            addUserData(request,data)
            if PagoPymentez.objects.filter(estado='success',detalle_estado='3').exists():
                data['generarform']=RangoFacturasForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/seguimiento_graduado_rangofecha.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))


