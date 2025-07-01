from datetime import datetime,timedelta
import json
import xlwt

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import TramitesporDepartamentoForm
from sga.models import convertir_fecha,TituloInstitucion,ReporteExcel, RubroEspecieValorada,Departamento,TipoEspecieValorada,AsistenteDepartamento,Persona
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action :
                inicio = request.POST['inicio']
                fin = request.POST['fin']
                try:
                    departamento= Departamento.objects.get(pk=request.POST['departamento'])
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)
                    m = 5
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Tramites por Departamento',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'Tramites Atendidos por Departamento', titulo2)
                    ws.write(3, 0, 'DESDE', titulo)
                    ws.write(3, 1, str((fechai.date())), titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, str((fechaf.date())), titulo)
                    ws.write(5, 0, 'DEPARTAMENTO: ', titulo)
                    ws.write(5, 1, elimina_tildes(departamento.descripcion), titulo)
                    ws.write(6, 0,  'ATENDIDO POR', titulo)
                    columna = 1
                    detalle = 5
                    fila = 7
                    totalasistente=0
                    tiposdetramites=RubroEspecieValorada.objects.filter(rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,rubro__cancelado=True,departamento=departamento,tipoespecie__es_especie=True).order_by('tipoespecie').distinct().values('tipoespecie')
                    for ttramite in TipoEspecieValorada.objects.filter(id__in=tiposdetramites):
                        # print(ttramite)
                        ws.write(6, columna,elimina_tildes(ttramite.nombre),titulo)
                        columna=columna+1
                    ws.write(6, columna,  'TOTAL', titulo)
                    for asistente in AsistenteDepartamento.objects.filter(departamento=departamento,activo=True).distinct().exclude(puedereasignar=True).order_by('persona'):
                        # print(asistente)
                        columna=0
                        ws.write(fila,0 ,elimina_tildes(asistente.persona.nombre_completo_inverso()))
                        for ttramite in TipoEspecieValorada.objects.filter(id__in=tiposdetramites):
                            cantidadtramites=  RubroEspecieValorada.objects.filter(rubro__fecha__gte=fechai,rubro__fecha__lte=fechaf,rubro__cancelado=True,departamento=departamento,tipoespecie=ttramite,usrasig=asistente.persona.usuario).count()
                            ws.write(fila,columna+1 ,cantidadtramites)
                            totalasistente+=cantidadtramites
                            columna=columna+1
                        ws.write(fila,columna+1,totalasistente,titulo)
                        fila = fila +1
                        totalasistente=0
                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='tramitesxcoordinacion'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex) + " ")
                    return HttpResponse(json.dumps({"result":str(ex) }),content_type="application/json")
        else:
            data = {'title': 'Resumen de Tramites por Departamento'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                reportes = ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists()
                if Persona.objects.filter(usuario=request.user).exists():
                    persona=Persona.objects.get(usuario=request.user)
                    if not persona.usuario.is_superuser:
                        departamento=Departamento.objects.filter(id__in=AsistenteDepartamento.objects.filter(persona__usuario=request.user).values('departamento__id'))
                        data['reportes'] = reportes
                        data['generarform']=TramitesporDepartamentoForm(initial={'departamento': departamento, 'inicio':datetime.now().date(),'fin':datetime.now().date()})
                        data['generarform'].for_departamento(departamento)
                    else:
                        data['reportes'] = reportes
                        data['generarform']=TramitesporDepartamentoForm(initial={'inicio':datetime.now().date(),'fin':datetime.now().date()})
                return render(request ,"reportesexcel/xls_especiesvaloradasxdepartamento.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

