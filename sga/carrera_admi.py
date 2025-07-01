import datetime
from datetime import datetime, timedelta
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Avg
from django.db.models.aggregates import Sum
from django.db import transaction
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from django.template import RequestContext
from decorators import secure_module
from settings import CENTRO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_INSCRIPCION, DEFAULT_PASSWORD, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, UTILIZA_GRUPOS_ALUMNOS, REPORTE_CERTIFICADO_INSCRIPCION, EMAIL_ACTIVE, EVALUACION_ITB, REGISTRO_HISTORIA_NOTAS, NOTA_ESTADO_EN_CURSO, GENERAR_RUBROS_PAGO, GENERAR_RUBRO_INSCRIPCION, GENERAR_RUBRO_INSCRIPCION_MARGEN_DIAS, MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITS, UTILIZA_NIVEL0_PROPEDEUTICO, TIPO_PERIODO_PROPEDEUTICO, NOTA_ESTADO_APROBADO, UTILIZA_FICHA_MEDICA, EVALUACION_TES, CORREO_INSTITUCIONAL, USA_CORREO_INSTITUCIONAL, INSCRIPCION_CONDUCCION, NIVEL_MALLA_CERO
from sga.alu_malla import aprobadaAsignatura
from sga.commonviews import addUserData, ip_client_address
from sga.docentes import calculate_username
from sga.finanzas import convertir_fecha

from sga.forms import CarreraForm,  CarreraCulminacionForm
from sga.models import Carrera,Malla, Matricula, TipoOtroRubro, Inscripcion, Rubro, RubroOtro, RubroMasivo, DetalleRubroMasivo, TipoCulminacionEstudio
from sga.tasks import gen_passwd


class MiPaginador(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador,self).__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left<1:
            left=1
        if right>self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right+1)
        self.primera_pagina = True if left>1 else False
        self.ultima_pagina = True if right<self.num_pages else False
        self.ellipsis_izquierda = left-1
        self.ellipsis_derecha = right+1



@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action=='add':
                if int(request.POST['edit'])== 0:
                    f = CarreraForm(request.POST)
                else :
                    f = CarreraForm(request.POST, instance=Carrera.objects.get(pk=request.POST['edit']))
                if f.is_valid():
                    f.save()


                return HttpResponseRedirect("/carrera_admi")

            elif action == 'activacion':
                try:
                    d = Carrera.objects.get(pk=request.POST['id'])
                    if not Malla.objects.filter(vigente=True,carrera=d).exists():
                        if d.activo:
                            d.activo = False
                        else:
                            d.activo = True
                        d.save()
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'activaronline':
                try:
                    d = Carrera.objects.get(pk=request.POST['id'])
                    if d.online:
                        d.online = False
                    else:
                        d.online = True
                    d.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'activarhibrido':
                try:
                    d = Carrera.objects.get(pk=request.POST['id'])
                    if d.hibrido:
                        d.hibrido = False
                    else:
                        d.hibrido = True
                    d.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'generarrubro':
                try:
                    carrera = Carrera.objects.get(pk=request.POST['id'])
                    rm = RubroMasivo(carrera=carrera,
                                     descripcion=request.POST['rubro'],
                                     fecha= datetime.now().date(),
                                     usuario=request.user)
                    rm.save()
                    con=0
                    for m in Matricula.objects.filter(inscripcion__carrera=carrera,nivel__cerrado=False).exclude(nivel__nivelmalla__id__in=(NIVEL_MALLA_CERO,10)):
                        if m.inscripcion.matriculado():
                            tipootro = TipoOtroRubro.objects.get(pk=7)
                            inscripcion = m.inscripcion
                            rubro = Rubro(fecha=datetime.now().date(), valor=float(request.POST['valor']),
                                inscripcion=inscripcion, cancelado=False, fechavence=convertir_fecha(request.POST['fecha']))
                            rubro.save()
                            rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion=request.POST['rubro'])
                            rubrootro.save()
                            drm = DetalleRubroMasivo(rubromasivo=rm,
                                                     rubrootro=rubrootro)
                            drm.save()
                            con=con +1
                    return HttpResponse(json.dumps({"result":"ok","contador":str(con)}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == 'adicionar':
                try:
                    rm =  RubroMasivo.objects.get(pk=request.POST['id'])
                    carrera = rm.carrera
                    con = 0
                    for m in Matricula.objects.filter(inscripcion__carrera=carrera,nivel__cerrado=False).exclude(nivel__nivelmalla__id__in=(NIVEL_MALLA_CERO,10)):
                        if m.inscripcion.matriculado():
                            if not DetalleRubroMasivo.objects.filter(rubromasivo=rm,rubrootro__rubro__inscripcion=m.inscripcion).exists():
                                if DetalleRubroMasivo.objects.filter(rubromasivo=rm).exists():
                                    dr=DetalleRubroMasivo.objects.filter(rubromasivo=rm)[:1].get()
                                    rotro= RubroOtro.objects.get(pk=dr.rubrootro.id)
                                    tipootro = TipoOtroRubro.objects.get(pk=7)
                                    inscripcion = m.inscripcion
                                    rubro = Rubro(fecha=datetime.now().date(), valor=rotro.rubro.valor,
                                        inscripcion=inscripcion, cancelado=False, fechavence=rotro.rubro.fechavence)
                                    rubro.save()
                                    rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion=rotro.descripcion)
                                    rubrootro.save()
                                    drm = DetalleRubroMasivo(rubromasivo=rm,
                                                             rubrootro=rubrootro)
                                    drm.save()
                                    con=con +1
                    return HttpResponse(json.dumps({"result":"ok","contador":str(con)}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            return HttpResponseRedirect("/carrera_admi")
        else:
            data = {'title': 'Listado de Carreras'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action=='add':
                    data['title'] = 'Nuevo Carrera'
                    carrera = CarreraForm()
                    data['form'] = carrera
                    data['titulo'] = 'Adicionar Nueva Carrera'
                    data['editar']  = 0
                    return render(request ,"carrera_admi/add_carrera.html" ,  data)

                elif action=='edit':
                    data['title'] = 'Editar Carrera'
                    carrera = Carrera.objects.get(pk=request.GET['id'])
                    carreraf = CarreraForm(instance=carrera)
                    data['form'] = carreraf
                    data['titulo'] = 'Editar Carrera'
                    data['editar']  = carrera.id
                    return render(request ,"carrera_admi/add_carrera.html" ,  data)

                elif action == 'rubroscreados':
                    carrera =  Carrera.objects.get(pk=request.GET['id'])
                    data['rubros'] = RubroMasivo.objects.filter(carrera=carrera)
                    data['carrera'] = carrera
                    return render(request ,"carrera_admi/carrera_rubros.html" ,  data)




                elif action == 'eliminarubro':
                    try:
                        rm =  RubroMasivo.objects.get(pk=request.GET['id'])
                        carrera = rm.carrera
                        if DetalleRubroMasivo.objects.filter(rubromasivo=rm).exists():
                            drm = DetalleRubroMasivo.objects.filter(rubromasivo=rm).values('rubrootro_id')
                            rubro = RubroOtro.objects.filter(pk__in=drm).values('rubro')
                            rotro = RubroOtro.objects.filter(pk__in=drm,rubro__cancelado=False)
                            r=Rubro.objects.filter(pk__in=rubro,cancelado=False)
                            r.delete()
                            rotro.delete()
                        rm.delete()
                        return HttpResponseRedirect("/carrera_admi?action=rubroscreados&id="+str(carrera.id))
                    except Exception as ex:
                        pass

                elif action == 'ver':
                    rm =  RubroMasivo.objects.get(pk=request.GET['id'])
                    data['rubros'] = DetalleRubroMasivo.objects.filter(rubromasivo=rm).order_by('rubrootro__rubro__inscripcion__persona__apellido1')
                    data['rubromasivo'] = rm
                    return render(request ,"carrera_admi/ver_estudiantes.html" ,  data)

                elif action=='delete':
                    data['title'] = 'Eliminar Carrera'
                    carrera = Carrera.objects.get(pk=request.GET['id'])
                    carrera.delete()
                    return HttpResponseRedirect('/carrera_admi')



            else:
                search = None
                todos = None

                if 's' in request.GET:
                    search = request.GET['s']
                if 't' in request.GET:
                    todos = request.GET['t']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    carrera = Carrera.objects.filter(Q(nombre__icontains=search) | Q(alias__icontains=search) | Q(titulo__icontains=search)).order_by('nombre')
                    # else:
                    #     visitabiblioteca = VisitaBiblioteca.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1])).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                else:
                     carrera = Carrera.objects.all().order_by('nombre')

                paging = MiPaginador(carrera, 15)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(p)

                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['todos'] = todos if todos else ""
                data['carrera'] = page.object_list
                data['fecha'] = datetime.now().date()
                tipo = CarreraCulminacionForm()
                data['tipoform'] = tipo
                return render(request ,"carrera_admi/carrera_admi.html" ,  data)

    except:
        return HttpResponseRedirect('/carrera_admi')
