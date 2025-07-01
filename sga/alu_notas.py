from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.context import RequestContext
import requests
from decorators import secure_module
from settings import REGISTRO_HISTORIA_NOTAS, VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, DEFAULT_PASSWORD
from sga.commonviews import addUserData
from sga.models import Inscripcion, RecordAcademico, HistoricoNotasITB, HistoricoRecordAcademico

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    data = {'title': 'Registro Academico'}
    addUserData(request, data)
    if 'action' in request.GET:
        action = request.GET['action']
        if action=='historiconotas':
            data['title'] = 'Historico de Notas del Alumno'
            inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
            historicos = HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion).order_by('fecha')
            paging = Paginator(historicos, 40)
            try:
                p = 1
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)
            data['paging'] = paging
            data['page'] = page
            data['historicos'] = page.object_list
            data['inscripcion'] = inscripcion
            data['historia_notas'] = REGISTRO_HISTORIA_NOTAS
            if DEFAULT_PASSWORD == 'itb':
                        try:
                            if inscripcion.persona.extranjero:
                                ced = inscripcion.persona.pasaporte
                                op=0
                            else:
                                op=1
                                ced = inscripcion.persona.cedula
                            datos = requests.get('http://sga.buckcenter.com.ec/api',params={'a': 'datos_ingles', 'ced':ced , 'op':op })
                            if datos.status_code==200:
                                data['otrasnotas']=datos.json()['notas']
                        except Exception as e:
                            pass
            return render(request ,"alu_notas/historiconotasbs.html" ,  data)
    else:
        try:
            inscripcion = Inscripcion.objects.get(persona=data['persona'])

            #Comprobar que no tenga deudas para que no pueda usar el sistema
            if VALIDAR_ENTRADA_SISTEMA_CON_DEUDA and inscripcion.tiene_deuda():
                return HttpResponseRedirect("/")

            records = RecordAcademico.objects.filter(inscripcion=inscripcion).order_by('fecha')
            paging = Paginator(records, 40)
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)
            data['paging'] = paging
            data['page'] = page
            data['records'] = page.object_list
            data['historia_notas'] = REGISTRO_HISTORIA_NOTAS
            data['inscripcion'] = inscripcion
            if DEFAULT_PASSWORD == 'itb':
                        try:
                            if inscripcion.persona.extranjero:
                                ced = inscripcion.persona.pasaporte
                                op=0
                            else:
                                op=1
                                ced = inscripcion.persona.cedula
                            datos = requests.get('http://sga.buckcenter.com.ec/api',params={'a': 'datos_ingles', 'ced':ced , 'op':op })
                            if datos.status_code==200:
                                data['otrasnotas']=datos.json()['notas']
                        except Exception as e:
                            pass
            return render(request ,"alu_notas/recordbs.html" ,  data)
        except :
            return HttpResponseRedirect("/")