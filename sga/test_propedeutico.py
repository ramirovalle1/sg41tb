import json
import random
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.db.models.expressions import F
from django.core.paginator import Paginator
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
import psycopg2
from decorators import secure_module
from django.db.models.query_utils import Q
from sga.commonviews import addUserData,ip_client_address
from django.utils.encoding import force_str
from django.template import RequestContext
from sga.forms import TipoTestForm, InstruccionTestForm, EjercicioTestForm, ParametroTestForm, AreaTestForm, PreguntaTestForm, ObservacionTestForm,EjercicioTestPersonalidadForm
from sga.models import Periodo, AmbitoEvaluacion, AmbitoInstrumentoEvaluacion, IndicadorEvaluacion, IndicadorAmbitoInstrumentoEvaluacion,\
    Clase, CoordinadorCarrera, Profesor, EvaluacionProfesor, Matricula, MateriaAsignada,\
    DatoInstrumentoEvaluacion, DIAS_EVALUACION, TipoTest, InscripcionTipoTest, InstruccionTest, EjercicioTest, ParametroTest,\
    PreguntaTest, AreaTest,Inscripcion,RespuestaTest,Persona, Carrera, PuntoBaremo
from settings import TIPO_PERIODO_PROPEDEUTICO, TEST_VOCACIONAL,EMAIL_ACTIVE, CARRERAS_ID_EXCLUIDAS_INEC,TIPO_PERIODO_REGULAR


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

def convertDate(s):
    d = int(s[0:2])
    m = int(s[3:5])
    y = int(s[6:])
    return datetime.date(y,m,d)

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'activacion':
                d = TipoTest.objects.get(pk=request.POST['id'])
                if (d.ejercicio_test() and d.instrucion_test()) or (d.pregunta_test() ):
                    d.estado = not d.estado
                    d.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(d).pk,
                        object_id       = d.id,
                        object_repr     = force_str(d),
                        action_flag     = ADDITION,
                        change_message  = 'Activacion o desacti Test (' + client_address + ')' )
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == 'add':
                f = TipoTestForm(request.POST)
                if f.is_valid():
                    tipotest = TipoTest(
                        descripcion = f.cleaned_data['descripcion'],
                        descripcioncorta = f.cleaned_data['descripcioncorta'],
                        minutofin = f.cleaned_data['minutofin'],
                        observacion = f.cleaned_data['observacion'],
                        estado = f.cleaned_data['estado'],
                        personalidad = f.cleaned_data['personalidad']
                    )

                    tipotest.save()
                    # Log de ADICIONAR INSCRIPCION
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tipotest).pk,
                        object_id       = tipotest.id,
                        object_repr     = force_str(tipotest),
                        action_flag     = ADDITION,
                        change_message  = 'Test Agregado (' + client_address + ')' )

            elif action == 'edit':
                f = TipoTestForm(request.POST)
                test = TipoTest.objects.get(pk=request.POST['test'])
                if f.is_valid():
                    test.descripcion = f.cleaned_data['descripcion']
                    test.descripcioncorta = f.cleaned_data['descripcioncorta']
                    test.minutofin = f.cleaned_data['minutofin']
                    test.observacion = f.cleaned_data['observacion']
                    test.personalidad = f.cleaned_data['personalidad']
                    test.save()
                    # Log de EDITAR TEST
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(test).pk,
                        object_id       = test.id,
                        object_repr     = force_str(test),
                        action_flag     = CHANGE,
                        change_message  = 'Test Modificado (' + client_address + ')' )

            elif action == 'addinstruccion':
                f = InstruccionTestForm(request.POST,request.FILES)
                if f.is_valid():
                    instruccion = InstruccionTest(
                        tipotest = f.cleaned_data['tipotest'],
                        imagen = request.FILES['imagen'],
                        ejemplo = f.cleaned_data['ejemplo'],
                        explicacion = f.cleaned_data['explicacion']
                    )

                    instruccion.save()
                    # Log de ADICIONAR INSCRIPCION
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(instruccion).pk,
                        object_id       = instruccion.id,
                        object_repr     = force_str(instruccion),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionada Instruccion (' + client_address + ')' )
                    return HttpResponseRedirect("/test_propedeutico?action=editar&test="+str(request.POST['test'])+'&ver=0')
            elif action == 'addpregunta':
                f = PreguntaTestForm(request.POST)
                if f.is_valid():
                    pregunta=""
                    test = TipoTest.objects.get(pk=request.POST['test'])
                    if int(request.POST['edit'])== 0:
                        pregunta = PreguntaTest(
                            tipotest = test,
                            areatest = f.cleaned_data['areatest'],
                            pregunta = f.cleaned_data['pregunta'],
                            tipo = f.cleaned_data['tipo'],
                            orden = f.cleaned_data['orden']
                        )
                    else:

                       pregunta = PreguntaTest.objects.get(pk=request.POST['edit'])
                       pregunta.tipotest = test
                       pregunta.areatest = f.cleaned_data['areatest']
                       pregunta.pregunta = f.cleaned_data['pregunta']
                       pregunta.tipo = f.cleaned_data['tipo']
                       pregunta.orden = f.cleaned_data['orden']

                    pregunta.save()
                    # Log de ADICIONAR INSCRIPCION
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pregunta).pk,
                        object_id       = pregunta.id,
                        object_repr     = force_str(pregunta),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionada Pregunta (' + client_address + ')' )
                    return HttpResponseRedirect("/test_propedeutico?action=editar&test="+str(request.POST['test'])+'&ver=0')
            elif action == 'editinstruccion':
                instr = InstruccionTest.objects.get(pk=request.POST['ins'])
                test = TipoTest.objects.get(pk=instr.tipotest.id)
                f = InstruccionTestForm(request.POST)
                if f.is_valid():
                    if str(request.POST['mod'])== '1':
                        instr.ejemplo=f.cleaned_data['ejemplo']
                    elif str(request.POST['mod'])== '2':
                        instr.imagen=request.FILES['imagen']
                    elif str(request.POST['mod'])== '3':
                        instr.explicacion=f.cleaned_data['explicacion']
                    instr.save()
                    # Log de ADICIONAR INSCRIPCION
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(instr).pk,
                        object_id       = instr.id,
                        object_repr     = force_str(instr),
                        action_flag     = ADDITION,
                        change_message  = 'Edita Instruccion (' + client_address + ')' )
                    return HttpResponseRedirect("/test_propedeutico?action=editar&test="+str(test.id)+'&ver=0')

            elif action == 'addejercicio':
                test = TipoTest.objects.get(pk=request.POST['test'])
                ejercicio=''
                if not test.personalidad:
                    f = EjercicioTestForm(request.POST,request.FILES)
                    if f.is_valid():
                        ejercicio = EjercicioTest(
                            tipotest = test,
                            imagen = request.FILES['imagen'],
                            parametrotest = f.cleaned_data['parametrotest']
                        )

                        ejercicio.save()
                else:
                    f = EjercicioTestPersonalidadForm(request.POST,request.FILES)
                    if f.is_valid():
                        ejercicio = EjercicioTest(
                            tipotest = test,
                            pregunta = f.cleaned_data['pregunta'],
                            parametrotest = f.cleaned_data['parametrotest']
                        )

                        ejercicio.save()

                # Log de ADICIONAR EJERCICIO TEST
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(ejercicio).pk,
                    object_id       = ejercicio.id,
                    object_repr     = force_str(ejercicio),
                    action_flag     = ADDITION,
                    change_message  = 'Ejercicio Adicionado (' + client_address + ')' )
                return HttpResponseRedirect("/test_propedeutico?action=ejercicio&test="+str(request.POST['test'])+'&ver=0')

            elif action == 'editejer':
                ejer = EjercicioTest.objects.get(pk=request.POST['ejer'])
                test = TipoTest.objects.get(pk=ejer.tipotest.id)
                if not test.personalidad:
                    f = EjercicioTestForm(request.POST)
                    if f.is_valid():
                        ejer.imagen=request.FILES['imagen']
                        ejer.parametrotest=f.cleaned_data['parametrotest']
                        ejer.save()
                else:
                    f = EjercicioTestPersonalidadForm(request.POST)
                    if f.is_valid():
                        ejer.parametrotest=f.cleaned_data['parametrotest']
                        ejer.pregunta=f.cleaned_data['pregunta']
                        ejer.save()
                # Log de EDITAR EJERCICIO
                client_address = ip_client_address(request)
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(ejer).pk,
                    object_id       = ejer.id,
                    object_repr     = force_str(ejer),
                    action_flag     = CHANGE,
                    change_message  = 'Edita Ejercicio (' + client_address + ')' )
                return HttpResponseRedirect("/test_propedeutico?action=ejercicio&test="+str(test.id)+"&ver=0")

            elif action=='addparametro':
                if int(request.POST['edit'])== 0:
                    f=ParametroTestForm(request.POST)
                else:
                    f = ParametroTestForm(request.POST, instance=ParametroTest.objects.get(pk=request.POST['edit']))
                if f.is_valid():
                    f.save()
                    return HttpResponseRedirect("/test_propedeutico?action=parametro")

            elif action=='addarea':
                if int(request.POST['edit'])== 0:
                    f=AreaTestForm(request.POST)
                else:
                    f = AreaTestForm(request.POST, instance=AreaTest.objects.get(pk=request.POST['edit']))
                if f.is_valid():
                    f.save()
                    return HttpResponseRedirect("/test_propedeutico?action=area")

            elif action=='observacion':
                inscripciontest=InscripcionTipoTest.objects.get(pk=request.POST['id'])
                personaobs=Persona.objects.get(usuario=request.user)
                f = ObservacionTestForm(request.POST)
                if f.is_valid():
                    inscripciontest.observacion = f.cleaned_data['motivo']
                    inscripciontest.estado = True
                    inscripciontest.save()
                    if inscripciontest.inscripcion.persona.emailinst:
                        # /////////OOOOJJOOOOOOO/////
                        # persona= Persona.objects.get(pk=22968)
                        # email = persona.emailinst
                        email = inscripciontest.inscripcion.persona.emailinst
                        if EMAIL_ACTIVE:
                            if not inscripciontest.inscripcion.tienediscapacidad:
                                inscripciontest.mail_ingreobservacion(email, inscripciontest)
                            else:
                                inscripciontest.mail_ingreobservaciondiscapacidad(email, inscripciontest,personaobs.emailinst)
                    # Log de ADICIONAR INSCRIPCION
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(inscripciontest).pk,
                        object_id       = inscripciontest.id,
                        object_repr     = force_str(inscripciontest),
                        action_flag     = ADDITION,
                        change_message  = 'Ingresar Observacion (' + client_address + ')' )
                return HttpResponseRedirect("/test_propedeutico?action=alumnostest")


            return HttpResponseRedirect("/test_propedeutico")
        else:
            data = {'title': 'Proceso de Evaluacion de Docentes'}
            addUserData(request,data)
            data['proceso'] = data['periodo'].proceso_evaluativo()
            if data['periodo'].tipo.id == TIPO_PERIODO_REGULAR:
                if 'action' in request.GET:
                    action = request.GET['action']
                    if action=="add":
                        # data = {'title': 'Ingreso de Test'}
                        form = TipoTestForm()
                        data['form']=form
                        return render(request ,"test_propedeutico/addtest.html" ,  data)

                    elif action=="edit":
                        # data = {'title': 'Editar de Test'}
                        test = TipoTest.objects.get(pk=request.GET['id'])
                        form = TipoTestForm(initial={'descripcion':test.descripcion,'descripcioncorta':test.descripcioncorta,'minutofin':test.minutofin,'observacion':test.observacion,'personalidad':test.personalidad})
                        data['form']=form
                        data['test']=test
                        return render(request ,"test_propedeutico/edittipotest.html" ,  data)
                    elif action=="addejercicio":
                        # data = {'title': 'Ingreso de Ejercicio'}
                        test=TipoTest.objects.get(pk=request.GET['test'])
                        if not test.personalidad:
                            form = EjercicioTestForm()
                            data['form']=form
                            data['test']=test
                        else:
                            form = EjercicioTestPersonalidadForm()
                            data['form']=form
                            data['test']=test
                        return render(request ,"test_propedeutico/addejercicio.html" ,  data)

                    elif action=="editejer":
                        # data = {'title': 'Editar de ejercicio'}
                        ejer = EjercicioTest.objects.get(pk=request.GET['ejer'])
                        test = ejer.tipotest
                        if not test.personalidad:
                            form = EjercicioTestForm(initial={'imagen':ejer.imagen,'parametrotest':ejer.parametrotest})
                        else:
                            form = EjercicioTestPersonalidadForm(initial={'pregunta':ejer.pregunta,'parametrotest':ejer.parametrotest})
                        data['form']=form
                        data['ejer']=ejer
                        return render(request ,"test_propedeutico/editejercicio.html" ,  data)

                    elif action=='ejercicio':
                        # Instrumento 2 (Docentes)
                        test=TipoTest.objects.get(pk=request.GET['test'])
                        data['test'] = test
                        data['ver'] = request.GET['ver']
                        data['ejercicio'] = EjercicioTest.objects.filter(tipotest=test).order_by('id')
                        return render(request ,"test_propedeutico/ejercicio.html" ,  data)

                    elif action=="addinstruccion":
                        # data = {'title': 'Ingreso de Instruccion'}
                        test=TipoTest.objects.get(pk=request.GET['test'])
                        form = InstruccionTestForm()
                        form.consulta_tip(test)
                        data['form']=form
                        data['test']=test
                        return render(request ,"test_propedeutico/addinstruccion.html" ,  data)

                    elif action=="addvocacional":
                        # data = {'title': 'Ingreso de test Vocacional'}
                        test=TipoTest.objects.get(pk=request.GET['test'])
                        form = PreguntaTestForm()
                        data['form']=form
                        data['test']=test
                        data['edit']=0
                        data['area']=0
                        return render(request ,"test_propedeutico/addpregunta.html" ,  data)

                    elif action=="editinstruccion":
                        # data = {'title': 'Editar Instruccion'}
                        instr=InstruccionTest.objects.get(pk=request.GET['instruc'])
                        test=TipoTest.objects.get(pk=instr.tipotest.id)
                        form = ""
                        if str(request.GET['edi'])== '1':
                            data['val']= request.GET['edi']
                            form = InstruccionTestForm(initial={'ejemplo':instr.ejemplo,'imagen':instr.imagen,'explicacion':instr.explicacion,'tipotest':instr.tipotest})
                        elif str(request.GET['edi'])== '2':
                            data['val']= request.GET['edi']
                            form = InstruccionTestForm(initial={'ejemplo':instr.ejemplo,'imagen':instr.imagen,'explicacion':instr.explicacion,'tipotest':instr.tipotest})
                        elif str(request.GET['edi'])== '3':
                            data['val']= request.GET['edi']
                            form = InstruccionTestForm(initial={'ejemplo':instr.ejemplo,'imagen':instr.imagen,'explicacion':instr.explicacion,'tipotest':instr.tipotest})
                        data['form']=form
                        data['test']=test
                        data['ins']=instr
                        return render(request ,"test_propedeutico/editinstruccion.html" ,  data)

                    elif action=='editar':
                        # Instrumento 2 (Docentes)
                        test=TipoTest.objects.get(pk=request.GET['test'])
                        data['vocac']=0
                        form=""
                        if TEST_VOCACIONAL == test.id:
                            data['vocac']=1
                            form =PreguntaTest.objects.all().order_by('tipo','orden')
                        else:
                            form=InstruccionTest.objects.filter(tipotest=test).order_by('id')
                        data['test'] = test
                        data['ver'] = request.GET['ver']
                        data['instruciones'] = form
                        return render(request ,"test_propedeutico/editartest.html" ,  data)

                    elif action=='eliminartest':
                        # Instrumento 2 (Docentes)
                        test=TipoTest.objects.get(pk=request.GET['test'])
                        test.delete()
                        return HttpResponseRedirect("/test_propedeutico")

                    elif action=='eliminarejer':
                        # Instrumento 2 (Docentes)
                        ejer=EjercicioTest.objects.get(pk=request.GET['ejer'])
                        test = ejer.tipotest.id
                        ejer.delete()
                        return HttpResponseRedirect("/test_propedeutico?action=ejercicio&test="+str(test)+'&ver=0')

                    elif action=='parametro':
                        # Instrumento 2 (Docentes)
                        data['Title'] ='Parametro de Evaluacion'
                        data['parametro'] = ParametroTest.objects.all().order_by('id')
                        return render(request ,"test_propedeutico/parametro.html" ,  data)

                    elif action=='addparametro':
                        # Instrumento 2 (Docentes)
                        data['title'] = 'Adicionar Parametro'
                        data['titulo'] = 'Ingreso Parametro de Evaluacion'
                        data['form']= ParametroTestForm()
                        data['edit']= 0
                        return render(request ,"test_propedeutico/addparametro.html" ,  data)

                    elif action=='editparametro':
                        # Instrumento 2 (Docentes)
                        # data = {}
                        data['title'] = 'Editar Parametro'
                        parametro = ParametroTest.objects.get(pk=request.GET['id'])
                        form = ParametroTestForm(instance=parametro)
                        data['form'] = form
                        data['titulo'] = 'Editar Parametro de Evaluacion'
                        data['edit']  = parametro.id
                        return render(request ,"test_propedeutico/addparametro.html" ,  data)

                    elif action == 'eliminarpar':
                        param=ParametroTest.objects.get(pk=request.GET['par'])
                        param.delete()
                        return HttpResponseRedirect("/test_propedeutico?action=parametro")

                    elif action=='area':
                        # Instrumento 2 (Docentes)
                        # data = {'title': 'Areas Profesionales'}
                        data['areas'] = AreaTest.objects.all().order_by('pk')
                        return render(request ,"test_propedeutico/areatest.html" ,  data)

                    elif action=='addarea':
                        # Instrumento 2 (Docentes)
                        # data['title'] = 'Adicionar Area'
                        data['titulo'] = 'Ingreso de Area Profesional'
                        data['form']= AreaTestForm()
                        data['edit']= 0
                        return render(request ,"test_propedeutico/addarea.html" ,  data)

                    elif action=='editarea':
                        # Instrumento 2 (Docentes)
                        # data = {}
                        # data['title'] = 'Editar Area'
                        area = AreaTest.objects.get(pk=request.GET['id'])
                        form = AreaTestForm(instance=area)
                        data['form'] = form
                        data['titulo'] = 'Editar Area Profesional'
                        data['edit']  = area.id
                        return render(request ,"test_propedeutico/addarea.html" ,  data)

                    elif action == 'eliminararea':
                        area=AreaTest.objects.get(pk=request.GET['par'])
                        area.delete()
                        return HttpResponseRedirect("/test_propedeutico?action=area")

                    elif action == 'elimipregunta':
                        pregunta=PreguntaTest.objects.get(pk=request.GET['id'])
                        test=pregunta.tipotest.id
                        pregunta.delete()
                        return HttpResponseRedirect("/test_propedeutico?action=editar&test="+str(test)+'&ver=0')

                    elif action == 'editpregunta':
                        # data = {'title': 'Editar Instruccion'}
                        pre=PreguntaTest.objects.get(pk=request.GET['id'])
                        test=TipoTest.objects.get(pk=pre.tipotest.id)
                        form = PreguntaTestForm(initial={'orden':pre.orden,'pregunta':pre.pregunta,'tipo':pre.tipo,'areatest':pre.areatest})
                        data['form']=form
                        data['test']=test
                        data['ins']=pre
                        data['edit']=pre.id
                        data['area']= 0 if pre.areatest == None else 1
                        return render(request ,"test_propedeutico/addpregunta.html" ,  data)

                    elif action == 'alumnostest':
                        # data = {'title': 'Editar Instruccion'}
                        periodo = data['periodo']
                        if InscripcionTipoTest.objects.filter(inscripcion__matricula__in=Matricula.objects.filter(nivel__periodo=periodo)).exists():
                            inscripciontest=InscripcionTipoTest.objects.filter(inscripcion__matricula__in=Matricula.objects.filter(nivel__periodo=periodo))
                            # matricula = Matricula.objects.filter(nivel__periodo=periodo)
                            #############################################################################################

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
                                if len(ss)==1:
                                    inscripciontest = InscripcionTipoTest.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search) | Q(inscripcion__persona__pasaporte__icontains=search) ).order_by('inscripcion__persona__apellido1')
                                else:
                                    inscripciontest = InscripcionTipoTest.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0]) & Q(inscripcion__persona__apellido2__icontains=ss[1])).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

                            else:
                                inscripciontest=InscripcionTipoTest.objects.filter(inscripcion__matricula__in=Matricula.objects.filter(nivel__periodo=periodo)).order_by('inscripcion')


                            paging = MiPaginador(inscripciontest, 30)
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
                            data['inscripciontest'] = page.object_list
                            ####################################################################################################

                            # data['inscripciontest']= inscripciontest
                            data['tipotest']= TipoTest.objects.all().order_by('id')
                            data['inscr']= 0
                            return render(request ,"test_propedeutico/alummnotest.html" ,  data)
                        else:
                            return HttpResponseRedirect("/test_propedeutico")

                    elif action == 'resultalumno':
                        # data = {'title': 'Editar Instruccion'}
                        aretest=""
                        areas=""
                        test=""
                        inscripciontest=InscripcionTipoTest.objects.get(pk=request.GET['inscr'])
                        if RespuestaTest.objects.filter(inscripciontipotest=inscripciontest).exclude(tipotest__id=TEST_VOCACIONAL):
                            resptip = RespuestaTest.objects.filter(inscripciontipotest=inscripciontest).exclude(tipotest__id=TEST_VOCACIONAL).values('tipotest').distinct('tipotest')
                            test = TipoTest.objects.filter(id__in=resptip).exclude(pk=TEST_VOCACIONAL).order_by('pk')
                        if RespuestaTest.objects.filter(inscripciontipotest=inscripciontest,tipotest__id=TEST_VOCACIONAL,respuesta=1):
                            aretest = TipoTest.objects.get(pk=TEST_VOCACIONAL)
                            valarea=RespuestaTest.objects.filter(inscripciontipotest=inscripciontest,tipotest=TEST_VOCACIONAL,respuesta=1)
                            lista=[]
                            for are in valarea:
                                lista.append(int(are.ejerciciotest))
                            pregu=PreguntaTest.objects.filter(pk__in=lista).values('areatest').distinct()
                            areas= AreaTest.objects.filter(pk__in=pregu).order_by('pk')
                        respuesta= RespuestaTest.objects.filter(inscripciontipotest=inscripciontest).exclude(tipotest=TEST_VOCACIONAL).order_by('tipotest__id')


                        data['inscripciontest']=inscripciontest
                        data['test']=test
                        data['respuesta']=respuesta
                        data['aretest']=aretest
                        data['areas']=areas
                        data['res']=""
                        data['test_vocacional']=TEST_VOCACIONAL
                        return render(request ,"test_propedeutico/resultadotest.html" ,  data)

                    elif action=='observacion':
                        data['title'] = 'Ingresar Observacion'
                        inscripciontest=InscripcionTipoTest.objects.get(pk=request.GET['inscr'])
                        data['inscripciontest'] = inscripciontest
                        data['form'] = ObservacionTestForm()
                        return render(request ,"test_propedeutico/observacion.html" ,  data)

                    elif action=='estadistica':
                        data['title'] = 'Estadisticas del Test propedeutico'
                        periodo = data['periodo']
                        carreras = [c for c in Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('coordinacion')]
                        lista_carreras_dependencia = []

                        cn = psycopg2.connect("host=10.10.9.45 dbname=aok user=aok password=R0b3rt0.1tb$") #DATOS DE LA BASE
                        # cn = psycopg2.connect("host=localhost dbname=academico_10feb user=postgres password=sa port=5433")
                        cur = cn.cursor()
                        var = 0
                        area1= AreaTest.objects.get(id=1)
                        area2= AreaTest.objects.get(id=2)
                        area3= AreaTest.objects.get(id=3)
                        area4= AreaTest.objects.get(id=4)
                        area5= AreaTest.objects.get(id=5)
                        for c in carreras:
                            superior = 0
                            medio_supe = 0
                            normal = 0
                            medio_infe =0
                            infe = 0
                            if int(request.GET['idtes']) != TEST_VOCACIONAL:
                                try:
                                    cur.execute("SELECT (sp_estadistica_test("+str(request.GET['idtes']) + "," + str(periodo.id) +","+ str(c.id) +",'SUPERIOR',''))")
                                    superior = cur.fetchone()[0]
                                    cur.execute("SELECT (sp_estadistica_test("+str(request.GET['idtes']) + "," + str(periodo.id) +","+ str(c.id) +",'MEDIO SUPERIOR','SUPERIOR'))")
                                    medio_supe = cur.fetchone()[0]
                                    cur.execute("SELECT (sp_estadistica_test("+str(request.GET['idtes']) + "," + str(periodo.id) +","+ str(c.id) +",'NORMAL','MEDIO SUPERIOR'))")
                                    normal = cur.fetchone()[0]
                                    cur.execute("SELECT (sp_estadistica_test("+str(request.GET['idtes']) + "," + str(periodo.id) +","+ str(c.id) +",'MEDIO INFERIOR','NORMAL'))")
                                    medio_infe = cur.fetchone()[0]
                                    cur.execute("SELECT (sp_estadistica_test("+str(request.GET['idtes']) + "," + str(periodo.id) +","+ str(c.id) +",'INFERIOR','MEDIO INFERIOR'))")
                                    infe = cur.fetchone()[0]
                                    lista_carreras_dependencia.append((c.alias,superior, "SUPERIOR",medio_supe,"MEDIO SUPERIOR",normal,"NORMAL",medio_infe,"MEDIO INFERIOR",infe,"INFERIOR",c.id))
                                except:
                                    pass
                            else:
                                try:
                                    idtest=str(request.GET['idtes'])
                                    cur.execute("select cast(count(area) as int)AS numero,area from (select case when case when area1.num is null then 0 else area1.num end >= case when area2.num is null then 0 else area2.num end and case when area1.num is null then 0 else area1.num end >= case when area3.num is null then 0 else area3.num end and case when area1.num is null then 0 else area1.num end >= case when area4.num is null then 0 else area4.num end and case when area1.num is null then 0 else area1.num end >= case when area5.num is null then 0 else area5.num end  then 1 when case when area2.num is null then 0 else area2.num end >= case when area1.num is null then 0 else area1.num end and case when area2.num is null then 0 else area2.num end >= case when area3.num is null then 0 else area3.num end and case when area2.num is null then 0 else area2.num end >= case when area4.num is null then 0 else area4.num end and case when area2.num is null then 0 else area2.num end >= case when area5.num is null then 0 else area5.num end  then 2 when case when area3.num is null then 0 else area3.num end >= case when area1.num is null then 0 else area1.num end and case when area3.num is null then 0 else area3.num end >= case when area2.num is null then 0 else area2.num end and case when area3.num is null then 0 else area3.num end >= case when area4.num is null then 0 else area4.num end and case when area3.num is null then 0 else area3.num end >= case when area5.num is null then 0 else area5.num end  then 3 when case when area4.num is null then 0 else area4.num end >= case when area1.num is null then 0 else area1.num end and case when area4.num is null then 0 else area4.num end >= case when area2.num is null then 0 else area2.num end and case when area4.num is null then 0 else area4.num end >= case when area3.num is null then 0 else area3.num end and case when area4.num is null then 0 else area4.num end >= case when area5.num is null then 0 else area5.num end  then 4 when case when area5.num is null then 0 else area5.num end >= case when area1.num is null then 0 else area1.num end and case when area5.num is null then 0 else area5.num end >= case when area2.num is null then 0 else area2.num end and case when area5.num is null then 0 else area5.num end >= case when area4.num is null then 0 else area4.num end and case when area5.num is null then 0 else area5.num end >= case when area3.num is null then 0 else area3.num end  then 5 end as area from((select count(*) as num,inscripciontipotest_id from sga_respuestatest, sga_inscripciontipotest where tipotest_id="+str(idtest)+ " and respuesta = 1 and inscripciontipotest_id in (select id from sga_inscripciontipotest where inscripcion_id in (select inscripcion_id from sga_matricula  where nivel_id in (select id from sga_nivel  where periodo_id="+ str(periodo.id)+" and carrera_id =  "+ str(c.id)+"))) and ejerciciotest in (select id from sga_preguntatest where  areatest_id=1)  and sga_inscripciontipotest.id=sga_respuestatest.inscripciontipotest_id group by inscripciontipotest_id)) as area1 left join((select count(*) as num,inscripciontipotest_id from sga_respuestatest, sga_inscripciontipotest where tipotest_id="+str(idtest)+" and respuesta = 1 and inscripciontipotest_id in (select id from sga_inscripciontipotest where inscripcion_id in (select inscripcion_id from sga_matricula where nivel_id in (select id from sga_nivel  where periodo_id="+str(periodo.id)+" and carrera_id ="+str(c.id)+"))) and ejerciciotest in  (select id from sga_preguntatest where  areatest_id=2)  and sga_inscripciontipotest.id=sga_respuestatest.inscripciontipotest_id group by inscripciontipotest_id)) as area2 on area1.inscripciontipotest_id = area2.inscripciontipotest_id left join((select count(*) as num,inscripciontipotest_id from sga_respuestatest, sga_inscripciontipotest where tipotest_id="+str(idtest)+" and respuesta = 1 and inscripciontipotest_id in (select id from sga_inscripciontipotest where inscripcion_id in (select inscripcion_id from sga_matricula  where nivel_id in (select id from sga_nivel  where periodo_id="+str(periodo.id)+" and carrera_id = "+str(c.id)+"))) and ejerciciotest in  (select id from sga_preguntatest where  areatest_id=3) and sga_inscripciontipotest.id=sga_respuestatest.inscripciontipotest_id group by inscripciontipotest_id)) as area3 on area1.inscripciontipotest_id = area3.inscripciontipotest_id and area3.inscripciontipotest_id = area2.inscripciontipotest_id left join((select count(*) as num,inscripciontipotest_id from sga_respuestatest, sga_inscripciontipotest where tipotest_id="+str(idtest)+" and respuesta = 1 and inscripciontipotest_id in (select id from sga_inscripciontipotest where inscripcion_id in (select inscripcion_id from sga_matricula where nivel_id in (select id from sga_nivel where periodo_id="+str(periodo.id)+" and carrera_id = "+str(c.id)+"))) and ejerciciotest in (select id from sga_preguntatest where  areatest_id=4)  and sga_inscripciontipotest.id=sga_respuestatest.inscripciontipotest_id group by inscripciontipotest_id)) as area4 on area1.inscripciontipotest_id = area4.inscripciontipotest_id and area4.inscripciontipotest_id = area2.inscripciontipotest_id and area4.inscripciontipotest_id = area3.inscripciontipotest_id left join((select count(*) as num,inscripciontipotest_id from sga_respuestatest, sga_inscripciontipotest where tipotest_id="+str(idtest)+" and respuesta = 1 and inscripciontipotest_id in (select id from sga_inscripciontipotest where inscripcion_id in (select inscripcion_id from sga_matricula where nivel_id in (select id from sga_nivel where periodo_id="+str(periodo.id)+" and carrera_id = "+str(c.id)+"))) and ejerciciotest in (select id from sga_preguntatest where  areatest_id=5) and sga_inscripciontipotest.id=sga_respuestatest.inscripciontipotest_id group by inscripciontipotest_id)) as area5 on area1.inscripciontipotest_id = area5.inscripciontipotest_id and area5.inscripciontipotest_id = area2.inscripciontipotest_id and area5.inscripciontipotest_id = area3.inscripciontipotest_id and area5.inscripciontipotest_id = area4.inscripciontipotest_id) areas group by area order by area")
                                    for ent in cur:
                                       if ent[1]== 1:
                                           infe = ent[0]
                                       if ent[1]== 2:
                                           medio_infe = ent[0]
                                       if ent[1]== 3:
                                           normal = ent[0]
                                       if ent[1]== 4:
                                           medio_supe = ent[0]
                                       if ent[1]== 5:
                                           superior = ent[0]


                                    lista_carreras_dependencia.append((c.alias,superior,area5.nombre+' - '+ area5.descripcion,medio_supe,area4.nombre+' - '+area4.descripcion,normal,area3.nombre+' - '+area3.descripcion,medio_infe,area2.nombre+' - '+area2.descripcion,infe,area1.nombre+' - '+area1.descripcion,c.id))

                                except:
                                    pass
                        cur.close()
                        data['lista_carreras_dependencia'] = lista_carreras_dependencia
                        data['tipotest']= TipoTest.objects.get(id=request.GET['idtes'])
                        return render(request ,"test_propedeutico/graf_estadistico.html" ,  data)

                    elif action=='detalleresl':
                        data['title'] = 'Ingresar Observacion'
                        inscripciontest=InscripcionTipoTest.objects.get(pk=request.GET['inscr'])
                        test=TipoTest.objects.get(pk=request.GET['tes'])
                        if test.id == TEST_VOCACIONAL:
                            respuesta = RespuestaTest.objects.filter(tipotest=test,inscripciontipotest=inscripciontest)
                            lista=[]
                            for resp in respuesta:
                                lista.append(int(resp.ejerciciotest))
                            ejercicio = PreguntaTest.objects.filter(tipotest=test,pk__in=lista)
                            data['nume'] = 0
                        else:
                            respuesta = RespuestaTest.objects.filter(tipotest=test,inscripciontipotest=inscripciontest)
                            lista=[]
                            for resp in respuesta:
                                lista.append(int(resp.ejerciciotest))
                            ejercicio = EjercicioTest.objects.filter(tipotest=test,pk__in=lista)
                            data['nume'] = 1
                        data['ejercicio'] = ejercicio
                        data['respuesta'] = respuesta
                        data['parametro'] = ParametroTest.objects.all()
                        data['inscripciontest'] = inscripciontest
                        data['test'] = test
                        # data['form'] = ObservacionTestForm()
                        return render(request ,"test_propedeutico/detalletest.html" ,  data)
                    return HttpResponseRedirect("/test_propedeutico")
                else:

                    # Calculo de Evaluaciones por Coordinadores
                    periodo = data['periodo']

                    # Calculo de Evaluaciones por Alumnos
                    alumnos_eval=0
                    alumnos_total = Matricula.objects.filter(pk__in=Matricula.objects.filter(nivel__periodo=periodo)).count()
                    data['existe']=0
                    if InscripcionTipoTest.objects.filter(inscripcion__matricula__in=Matricula.objects.filter(nivel__periodo=periodo)).exists():
                        data['existe']=1
                        cn = psycopg2.connect("host=10.10.9.45 dbname=aok user=aok password=R0b3rt0.1tb$") #DATOS DE LA BASE
                        # cn = psycopg2.connect("host=localhost dbname=academico_10feb user=postgres password=sa port=5433")
                        cur = cn.cursor()
                        # cur.execute("select cast(count(numtest.inscr) as int) from sga_inscripciontipotest inner join (select cast(count(tipotest)as int) as tipo, testinscr.inscr from (select tipotest_id as tipotest , inscripciontipotest_id as inscr from sga_respuestatest, sga_inscripciontipotest where inscripciontipotest_id in (select id from sga_inscripciontipotest where inscripcion_id in (select inscripcion_id from sga_matricula where nivel_id in (select id from sga_nivel where periodo_id=20 ))) and sga_inscripciontipotest.id=sga_respuestatest.inscripciontipotest_id group by inscripciontipotest_id,sga_inscripciontipotest.tipotest_id order by inscripciontipotest_id ,tipotest_id ) testinscr group by inscr) numtest on numtest.inscr = sga_inscripciontipotest.id where numtest.tipo >=  (select case when (select cast(count(id) as int)from sga_tipotest where estado=true) is null then 0 else (select cast(count(id) as int)from sga_tipotest where estado=true) end)")
                        cur.execute("select cast(count(numtest.inscr) as int) from sga_inscripciontipotest inner join (select cast(count(tipotest)as int) as tipo, testinscr.inscr from (select sga_inscripciontipotest.tipotest_id as tipotest , inscripciontipotest_id as inscr from sga_respuestatest, sga_inscripciontipotest where inscripciontipotest_id in (select id from sga_inscripciontipotest where inscripcion_id in (select inscripcion_id from sga_matricula where nivel_id in (select id from sga_nivel where periodo_id=20 ))) and sga_inscripciontipotest.id=sga_respuestatest.inscripciontipotest_id group by inscripciontipotest_id,sga_inscripciontipotest.tipotest_id order by inscripciontipotest_id ,sga_inscripciontipotest.tipotest_id ) testinscr group by inscr) numtest on numtest.inscr = sga_inscripciontipotest.id where numtest.tipo >=  (select case when (select cast(count(id) as int)from sga_tipotest where estado=true) is null then 0 else (select cast(count(id) as int)from sga_tipotest where estado=true) end)")
                        alumnos_eval  = cur.fetchone()[0]
                        cur.close()
                    #     valo = InscripcionTipoTest.objects.filter(inscripcion__matricula__in=Matricula.objects.filter(nivel__periodo=periodo))
                    #     for val in valo:
                    #         canresp = RespuestaTest.objects.filter(inscripciontipotest__id=val.id).distinct().values('tipotest').count()
                    #         cantipo = TipoTest.objects.filter(estado=True).count()
                    #         if canresp >= cantipo:
                    #             alumnos_eval=alumnos_eval+1

                    data['totalalumnos'] = alumnos_total
                    data['alumnosevaluados'] = alumnos_eval #colocar alumnos_eval
                    data['test'] = TipoTest.objects.all()
                    data['vocacional'] = TEST_VOCACIONAL
                    # data['persona']= data['persona']
                    return render(request ,"test_propedeutico/test_propedeutico.html" ,  data)
            else:

                return HttpResponseRedirect('/')
    except Exception as ex:
         return HttpResponseRedirect('/?info='+str(ex))










def test_dobe(request):
    try:
        periodo=request.session['periodo']
        p = request.session['persona']
        # if  Inscripcion.objects.filter(persona=p,matricula__in=Matricula.objects.filter(nivel__periodo=periodo),matricula__nivel__periodo__tipo__id=TIPO_PERIODO_PROPEDEUTICO).exists():
        if  Inscripcion.objects.filter(persona=p,matricula__in=Matricula.objects.filter(nivel__periodo=periodo),matricula__nivel__periodo__tipo__id=TIPO_PERIODO_REGULAR).exists():
            if request.method=='POST':
                # action = request.POST['action']
                # if action=='area':
                try:
                    inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
                    test = TipoTest.objects.get(pk=request.POST['test'])
                    inscripciontest = InscripcionTipoTest.objects.get(inscripcion=inscripcion)

                    for x, y in request.POST.iteritems():
                        if len(x)>5 and x[:5]=='valor':
                            # pregunta = PreguntaTest.objects.get(pk=x[5:])
                            if y=="":
                                y="0"
                            dato = RespuestaTest(inscripciontipotest=inscripciontest, tipotest=test, ejerciciotest=int(x[5:]), respuesta=int(y))
                            dato.save()
                    return HttpResponseRedirect("/test_dobe")
                except Exception as ex:
                    return HttpResponseRedirect("/")
                # return HttpResponseRedirect("/")
            else:

                try:
                    data = {'title': 'Test Psicologico '}
                    addUserData(request,data)
                    data['proceso'] = data['periodo'].proceso_evaluativo()
                    if request.method=='GET':
                        if request.GET !={}:
                            action = request.GET['action']
                            if action=="evaluartest":

                                try:
                                    test = TipoTest.objects.get(pk=request.GET['tes'])
                                    inscripcion = Inscripcion.objects.get(persona__usuario=request.user)
                                    if RespuestaTest.objects.filter(inscripciontipotest__inscripcion=inscripcion,tipotest=test).exists():
                                        tipo = RespuestaTest.objects.filter(inscripciontipotest__inscripcion=inscripcion).values('tipotest')
                                        test= TipoTest.objects.all().exclude(pk__in=tipo)[:1].get()
                                    if not test.personalidad:
                                        if test.id == TEST_VOCACIONAL or not RespuestaTest.objects.filter(inscripciontipotest__inscripcion=inscripcion,tipotest=TEST_VOCACIONAL).exists() :
                                            pregunta = PreguntaTest.objects.filter(tipo=2).order_by('orden')
                                            data['nume'] = 0
                                        else:
                                            # pregunta = EjercicioTest.objects.filter(tipotest=test).order_by('pk')
                                            pregunta = EjercicioTest.objects.filter(tipotest=test).order_by('?','pk')
                                            data['nume'] = 1
                                            data['parametro'] = ParametroTest.objects.all().order_by('id')
                                            data['minutos'] = test.minutofin-1
                                    else:
                                        pregunta = EjercicioTest.objects.filter(tipotest=test).order_by('?','pk')
                                        data['nume'] = 1
                                        data['parametro'] = ParametroTest.objects.filter(tipotest__personalidad=True).order_by('id')
                                        data['minutos'] = test.minutofin-1

                                    if not InscripcionTipoTest.objects.filter(inscripcion=inscripcion).exists():
                                        inscripciontest = InscripcionTipoTest(inscripcion = inscripcion,
                                                                          observacion = "",
                                                                          estado = False,
                                                                          fechainicio = datetime.now())
                                        inscripciontest.save()
                                    paging = MiPaginador(pregunta, 2)
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
                                    data['pregunta'] = pregunta
                                    data['inscripcion'] = inscripcion

                                    # data['persona'] = inscripcion.persona
                                    # data['profesor'] = profesor
                                    # data['ambitos'] = ambitos
                                    data['test'] = test
                                    data['fecha'] = datetime.now()
                                    return render(request ,"test_propedeutico/testevaluar.html" ,  data)
                                except Exception as ex:
                                    return HttpResponseRedirect("/")
                        else:
                            data = {'title': 'Proceso de Evaluacion de Docentes'}
                            addUserData(request,data)
                            test = TipoTest.objects.get(pk=TEST_VOCACIONAL)
                            inscripcion = Inscripcion.objects.get(persona__usuario=request.user)
                            if not TipoTest.objects.filter(pk=TEST_VOCACIONAL,estado=True).exists() or RespuestaTest.objects.filter(inscripciontipotest__inscripcion=inscripcion,tipotest=test).exists():
                                test =  TipoTest.objects.filter(estado=True)[:1].get()
                                if RespuestaTest.objects.filter(inscripciontipotest__inscripcion=inscripcion).exists():
                                    ttipo = RespuestaTest.objects.filter(inscripciontipotest__inscripcion=inscripcion).distinct().values('tipotest')
                                    if TipoTest.objects.filter(estado=True,pk__in=ttipo).count()!=TipoTest.objects.filter(estado=True).count():
                                        test = TipoTest.objects.filter(estado=True).exclude(pk__in=ttipo)[:1].get()
                                    else:
                                        inscr = InscripcionTipoTest.objects.get(inscripcion=inscripcion)
                                        inscr.horafin=datetime.now()
                                        inscr.save()
                                        return HttpResponseRedirect("/")
                            if test.id == TEST_VOCACIONAL:
                                pregunta = PreguntaTest.objects.filter(tipo=1).order_by('orden')
                                data['vocacional'] = 1
                            else:
                                pregunta = InstruccionTest.objects.filter(tipotest=test).order_by('id')
                                data['vocacional'] = 0


                            data['persona'] = request.user
                            data['pregunta'] = pregunta
                            data['test'] = test

                            return render(request ,"test_propedeutico/testpreguntas.html" ,  data)
                except Exception as ex:
                    return HttpResponseRedirect("/?info="+str(ex))
        else:
            return HttpResponseRedirect("/")
    except Exception as ex:
         return HttpResponseRedirect('/?info='+str(ex))