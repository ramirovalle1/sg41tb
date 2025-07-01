# -*- coding: latin-1 -*-
from datetime import datetime, timedelta
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.core.paginator import Paginator
from django.db.models.aggregates import Max
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import CALCULA_FECHA_FIN_MATERIA, REPORTE_CRONOGRAMA_MATERIAS, TIPO_PERIODO_PROPEDEUTICO, NIVEL_MALLA_CERO, EVALUACION_ITB, MODELO_EVALUACION, GENERAR_RUBROS_PAGO, EVALUACION_TES, EVALUACION_IGAD, ASIGNATURA_PRACTICA_CONDUCCION
from settings import CALCULA_FECHA_FIN_MATERIA, CENTRO_EXTERNO, REPORTE_CRONOGRAMA_MATERIAS, TIPO_PERIODO_PROPEDEUTICO, NIVEL_MALLA_CERO,\
    EVALUACION_ITB, MODELO_EVALUACION, GENERAR_RUBROS_PAGO, EVALUACION_TES,PORCIENTO_NOTA1,PORCIENTO_NOTA2,PORCIENTO_NOTA3,\
    PORCIENTO_NOTA4, PORCIENTO_NOTA5, PORCIENTO_RECUPERACION,NOTA_ESTADO_APROBADO,REGISTRO_HISTORIA_NOTAS,MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, EVALUACION_ITS
from sga.commonviews import addUserData, ip_client_address
from sga.forms import Inscripcion, NivelForm, NivelFormEdit, MateriaForm, NivelPropedeuticoForm, ProfesorMateriaFormAdd, PagoNivelForm, PagoNivelEditForm, AsignarMateriaGrupoForm, NivelLibreForm, AdicionarOtroRubroForm, MateriaFormCext, ObservacionAbrirMateriaForm, GrupoPracticaForm, PracticaForm, GrupoPracticaFormEdit, ClaseConduccionForm, HistoricoNotasPracticaForm
from sga.models import Periodo, Sede, Carrera, Nivel, Materia, Feriado, NivelMalla, Malla, AsignaturaNivelacionCarrera, ProfesorMateria, MateriaAsignada,\
    RecordAcademico, HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, HistoricoNotasITB, Clase, PagoNivel, Rubro, RubroMatricula, RubroCuota, Leccion,\
    AsistenciaLeccion, Coordinacion, NivelLibreCoordinacion, RubroOtro, GrupoPractica, Practica,TurnoPractica,ClaseConduccion,Vehiculo,Profesor, \
    AlumnoPractica,Asignatura,TipoEstado, HistoricoNotasPractica
from time import sleep
from settings import MODULO_FINANZAS_ACTIVO

def convert_fecha(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2]))

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':


            f = GrupoPracticaForm(request.POST)
            if f.is_valid():
                f.save()
                nivel = f.instance
                # nivel.actualizar_materias()
                # nivel.crea_cronograma_pagos()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR NIVEL
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(nivel).pk,
                    object_id       = nivel.id,
                    object_repr     = force_str(nivel),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Nivel (' + client_address + ')' )
                return HttpResponseRedirect("/practicasconduc")
                # return HttpResponseRedirect("/practicascondu?action=materias&id="+str(nivel.id))
            else:
                return HttpResponseRedirect("/practicasconduc?action=add&error=1")


        elif action=='edit':
            f = GrupoPracticaFormEdit(request.POST, instance=GrupoPractica.objects.get(pk=request.POST['id']))
            if f.is_valid():
                f.save()
                return HttpResponseRedirect("/practicasconduc")
            else:
                return HttpResponseRedirect("/practicasconduc?action=edit&id="+request.POST['id'])
        elif action=='delete':
            g = GrupoPractica.objects.get(pk=request.POST['id'])
            g.delete()
            return HttpResponseRedirect('/practicasconduc')
        elif action=='editpractica':
            f = PracticaForm(request.POST, instance=Practica.objects.get(pk=request.POST['id']))
            if f.is_valid():
                f.save()
                return HttpResponseRedirect('/practicasconduc?action=practicas&id='+str(f.instance.grupopracticas.id))
            else:
                return HttpResponseRedirect("/practicasconduc?action=editpractica&id="+request.POST['id']+"&error=1")



        elif action=='addclase':
            grupopractica = GrupoPractica.objects.get(pk=request.POST['nivel'])
            practica = Practica.objects.get(pk=request.POST['practica'])
            turnopractica = TurnoPractica.objects.get(pk=request.POST['turnopractica'])
            dia = request.POST['dia']
            band=0
            sesion = practica.grupopracticas.sesionpracticas
            if int(dia) < 9:
                for i in range(int(dia),8):
                    if sesion.clases_los_(i):
                        f = ClaseConduccionForm(request.POST, instance=ClaseConduccion(practica=practica, turnopractica=turnopractica, dia=i))
                        if f.is_valid():
                            f.save()
                            band +=1

                            #Obtain client ip address
                            client_address = ip_client_address(request)

                            # Log de ADICIONAR MATERIA
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(practica).pk,
                                object_id       = practica.id,
                                object_repr     = force_str(practica),
                                action_flag     = ADDITION,
                                change_message  = 'Adicionada clase conduccion (' + client_address + ')' )

            if band > 0:
                return HttpResponseRedirect('/practicasconduc?action=horario&id='+str(grupopractica.id)+'&practica='+str(practica.id)+'&ret=1')
                        # return render(request ,"/.html" ,  data)
            else:
                return HttpResponseRedirect('/practicasconduc')


        elif action=='editclase':
            f = ClaseConduccionForm(request.POST)
            if f.is_valid():
                clase = ClaseConduccion.objects.get(pk=request.POST['id'])
                sesion=clase.practica.grupopracticas.sesionpracticas
                editar = request.POST['edit']
                idclas=int(request.POST['id'])
                if editar=='prof':
                    clase.profesor = f.cleaned_data['profesor']
                else:
                    clase.vehiculo = f.cleaned_data['vehiculo']
                clase.save()
                if int(clase.dia) < 9:
                    for i in range(int(clase.dia),8):
                        if sesion.clases_los_(int(i)+1):
                            clase = ClaseConduccion.objects.get(pk=idclas+1)
                            if editar=='prof':
                                clase.profesor = f.cleaned_data['profesor']
                            else:
                                clase.vehiculo = f.cleaned_data['vehiculo']
                            clase.save()
                            idclas+=1
                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de EDITAR HORARIO CLASE
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(clase).pk,
                    object_id       = clase.id,
                    object_repr     = force_str(clase),
                    action_flag     = CHANGE,
                    change_message  = 'Modificado Horario Clase (' + client_address + ')'  )

                return HttpResponseRedirect("/practicasconduc?action=horario&id="+str(clase.practica.grupopracticas.id)+'&practica='+str(clase.practica.id)+'&ret=1')
            else:
                return HttpResponseRedirect("/practicasconduc?action=editclase&id="+str(request.POST['id']))


        elif action=='addpractica':
            grupopractica = GrupoPractica.objects.get(pk=request.POST['idnivel'])
            f = PracticaForm(request.POST, instance=Practica(grupopracticas=grupopractica))
            if f.is_valid():
                f.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR MATERIA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(grupopractica).pk,
                    object_id       = grupopractica.id,
                    object_repr     = force_str(grupopractica),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionada Materia (' + client_address + ')' )
                data={}
                data['title'] = 'Cronograma de Practicas'
                data['nivel'] = grupopractica
                practicas = Practica.objects.filter(grupopracticas=grupopractica).order_by('fechainicio')
                data['materias'] = practicas
                return render(request ,"practicasconduc/practicas.html" ,  data)
            else:
                return HttpResponseRedirect('/practicasconduc')

        elif action=='addhistorico':
            estado = False
            inscripcion = Inscripcion.objects.get(pk=request.POST['id'])
            # alumno = AlumnoPractica.objects.get(inscripcion=inscripcion)
            # practica = Practica.objects.get(claseconduccion__practica=alumno.claseconduccion.practica)
            asignatura = Asignatura.objects.get(pk=ASIGNATURA_PRACTICA_CONDUCCION)
            f = HistoricoNotasPracticaForm(request.POST)
            if f.is_valid():
                tipoestado = f.cleaned_data['estado']
                if tipoestado.id == NOTA_ESTADO_APROBADO:
                    estado = True
                historico = HistoricoRecordAcademico(inscripcion=inscripcion,
                                            asignatura=asignatura,
                                            nota=f.cleaned_data['notafinal'],
                                            asistencia=100,
                                            fecha=datetime.now(),
                                            aprobada=estado,
                                            convalidacion=False,
                                            pendiente=False)
                historico.save()


                record = RecordAcademico(inscripcion=historico.inscripcion, asignatura=historico.asignatura,
                                        nota=historico.nota, asistencia=historico.asistencia,
                                        fecha=historico.fecha, aprobada=historico.aprobada,
                                        convalidacion=False, pendiente=False)
                record.save()
                cod1=0
                cod2=0
                cod3=0
                cod4=0
                if f.cleaned_data['cod1'] != None:
                    cod1= f.cleaned_data['cod1'].id
                if f.cleaned_data['cod2'] != None:
                    cod2= f.cleaned_data['cod2'].id
                if f.cleaned_data['cod3'] != None:
                    cod3= f.cleaned_data['cod3'].id
                if f.cleaned_data['cod4'] != None:
                    cod4= f.cleaned_data['cod4'].id
                notas = HistoricoNotasPractica(
                                            historico=historico,
                                            responsable= f.cleaned_data['responsable'].id,
                                            evaluador= f.cleaned_data['evaluador'],
                                            n1=f.cleaned_data['n1'], cod1=cod1,
                                            n2=f.cleaned_data['n2'], cod2=cod2,
                                            n3=f.cleaned_data['n3'], cod3=cod3,
                                            n4=f.cleaned_data['n4'], cod4=cod4,
                                            n5=f.cleaned_data['n5'],
                                            total = f.cleaned_data['total'],
                                            recup = f.cleaned_data['recup'],
                                            notafinal = f.cleaned_data['notafinal'],
                                            estado = f.cleaned_data['estado'])
                notas.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR HISTORICO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(historico).pk,
                    object_id       = historico.id,
                    object_repr     = force_str(historico),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Historico y Registro (' + client_address + ')' )
                # return HttpResponseRedirect("/practicasconduc?action=consulta&practica="+str(practica.id))
                return HttpResponseRedirect("/inscripciones?s="+str(inscripcion.persona.cedula))

        return HttpResponseRedirect("/niveles")
    else:
        data = {'title': 'Secciones de Practicas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Adicionar Seccion de Practica'
                carrera = Carrera.objects.get(pk=request.GET['carrera'])
                sede = Sede.objects.get(pk=request.GET['sede'])
                periodo = Periodo.objects.get(pk=request.GET['periodo'])
                 # + timedelta(30)
                data['form'] = GrupoPracticaForm(instance=GrupoPractica(periodo=periodo,carrera=carrera, sede=sede, inicio=periodo.inicio, fin=periodo.fin))
                return render(request ,"practicasconduc/adicionarbs.html" ,  data)

            elif action=='edit':
                data['title'] = 'Editar Seccion'
                grupopractica = GrupoPractica.objects.get(pk=request.GET['id'])
                form = GrupoPracticaFormEdit(instance=grupopractica)
                # form.for_grupo(nivel.carrera)
                data['form'] = form

                data['nivel'] = grupopractica
                return render(request ,"practicasconduc/editarbs.html" ,  data)
            elif action=='del':
                data['title'] = 'Borrar Nivel Academico'
                grupopractica = GrupoPractica.objects.get(pk=request.GET['id'])
                data['nivel'] = grupopractica
                return render(request ,"practicasconduc/borrarbs.html" ,  data)

            elif action=='practicas':
                data['title'] = 'Cronograma de Practicas'
                grupopractica = GrupoPractica.objects.get(pk=request.GET['id'])
                data['nivel'] = grupopractica
                practicas = Practica.objects.filter(grupopracticas=grupopractica).order_by('fechainicio')
                data['materias'] = practicas
                data['error']=2
                if not TurnoPractica.objects.filter(sesionpracticas=grupopractica.sesionpracticas).exists():
                    data['error']=1
                return render(request ,"practicasconduc/practicas.html" ,  data)


            elif action=='editpractica':
                data['title'] = 'Editar Materia de Nivel Academico'
                practica = Practica.objects.get(pk=request.GET['id'])
                if not practica.fechainicio and not practica.fechafin:
                    practica.fechainicio = datetime.now()
                    practica.fechafin = datetime.now()
                data['materia'] = practica
                data['form'] = PracticaForm(instance=practica)
                data['materialibre'] = MODELO_EVALUACION==EVALUACION_TES
                return render(request ,"practicasconduc/edit_practica.html" ,  data)
            elif action=='addpractica':
                data['title'] = 'Adicionar Practica'
                data['nivel'] = GrupoPractica.objects.get(pk=request.GET['id'])
                data['form'] = PracticaForm(instance=Practica(grupopracticas=data['nivel'], fechainicio=data['nivel'].inicio, fechafin=data['nivel'].fin))
                data['action'] = 'addpractica'
                return render(request ,"practicasconduc/adicionar_practica.html" ,  data)
            elif action=='delepract':
                data['title'] = 'Adicionar Practica'
                practica= Practica.objects.get(pk=request.GET['id'])
                grupopractica = GrupoPractica.objects.get(pk=practica.grupopracticas.id)
                practica.delete()
                data['nivel'] = grupopractica
                practicas = Practica.objects.filter(grupopracticas=grupopractica).order_by('fechainicio')
                data['materias'] = practicas
                return render(request ,"practicasconduc/practicas.html" ,  data)
            elif action=='horario':
                ret = None
                # Editar un Horario
                data['title'] = 'Horario de Practicas De conduccion'
                grupopractica = GrupoPractica.objects.get(pk=request.GET['id'])
                practica = Practica.objects.get(pk=request.GET['practica'])
                data['nivel'] = grupopractica
                if 'ret' in request.GET:
                    ret = request.GET['ret']

                data['semana'] = ['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado','Domingo']
                data['turnos'] = TurnoPractica.objects.filter(sesionpracticas=data['nivel'].sesionpracticas).order_by('turno')
                data['clases'] = ClaseConduccion.objects.filter(practica__grupopracticas=grupopractica,practica=practica).order_by('-practica__fechainicio')
                data['practica'] = practica

                # data['materiasfaltantes'] = [x for x in nivel.materia_set.all() if x.clase_set.count()==0]
                data['ret'] = ret if ret else ""  #Para retornar a nivel y no a horarios
                data['cronogramapagos'] = MODELO_EVALUACION!=EVALUACION_TES
                return render(request ,"practicasconduc/horariobs.html" ,  data)

            elif action=='consulta':
                data['title'] = 'Listado de Alumnos en Practica'
                practica = Practica.objects.get(pk=request.GET['practica'])
                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                      ss.remove('')
                    if len(ss)==1:
                        claseconduccion = AlumnoPractica.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search)|Q(claseconduccion__profesor__persona__nombres__icontains=search) | Q(claseconduccion__profesor__persona__apellido1__icontains=search) | Q(claseconduccion__profesor__persona__apellido2__icontains=search) | Q(claseconduccion__profesor__persona__cedula__icontains=search)| Q(claseconduccion__vehiculo__placa__icontains=search)).order_by('inscripcion__persona__apellido1')
                    else:
                        claseconduccion = AlumnoPractica.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0], inscripcion__persona__apellido2__icontains=ss[1])|Q(claseconduccion__profesor__persona__apellido1__icontains=ss[0], claseconduccion__profesor__persona__apellido2__icontains=ss[1])).order_by('inscripcion__persona__apellido1')

                else:
                    claseconduccion= AlumnoPractica.objects.filter(claseconduccion__practica=practica)

                if 'g' in request.GET:
                    turnoid = request.GET['g']
                    claseconduccion = AlumnoPractica.objects.filter(claseconduccion__turnopractica__id=turnoid)
                    # data['turno']
                data['practica'] = practica
                data['fecha'] = datetime.date(datetime.now())
                data['turno'] = TurnoPractica.objects.filter(sesionpracticas=practica.grupopracticas.sesionpracticas).order_by('turno')
                data['clases'] = ClaseConduccion.objects.filter(practica=practica).order_by('-practica__fechainicio')
                data['alumnolistas'] =  claseconduccion
                return render(request ,"practicasconduc/listaalumnos.html" ,  data)
            elif action=='nota':
                data['title'] = 'Ingreso de Notas'
                # historia = HistoricoNotasITB.objects.get(pk=request.GET['id'])
                # initial = model_to_dict(historia)
                # alumno = AlumnoPractica.objects.get(pk=request.GET['id'])
                alumno = Inscripcion.objects.get(pk=request.GET['id'])
                # inscripcion = Inscripcion.objects.get(pk=alumno.inscripcion.id)
                data['nota1'] = PORCIENTO_NOTA1
                data['nota2']= PORCIENTO_NOTA2
                data['nota3']= PORCIENTO_NOTA3
                data['nota4']= PORCIENTO_NOTA4
                data['nota5']= PORCIENTO_NOTA5
                data['recup']= PORCIENTO_RECUPERACION
                data['form'] = HistoricoNotasPracticaForm()
                data['asignatura'] = Asignatura.objects.get(pk=ASIGNATURA_PRACTICA_CONDUCCION)
                data['alumno'] = alumno
                return render(request ,"practicasconduc/ingresonota.html" ,  data)
            elif action=='historico':
                data['title'] = 'Historico de Notas del Alumno'
                # alumno = AlumnoPractica.objects.get(pk=request.GET['id'])
                inscripcion = Inscripcion.objects.get(pk=request.GET['id'])

                search = None
                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    records = HistoricoRecordAcademico.objects.filter(Q(asignatura__nombre__icontains=search), inscripcion=inscripcion).order_by('fecha','asignatura','id')
                else:
                    addUserData(request,data)
                    persona=data['persona']
                    if persona.puede_editar_ingles():
                       records = HistoricoRecordAcademico.objects.filter(Q(asignatura__nombre__icontains='INGLES'), inscripcion=inscripcion).order_by('fecha','asignatura','id')
                    else:
                        records = HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion).order_by('fecha','asignatura','id')

                paging = Paginator(records, 30)
                try:
                    p = 1
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)
                data['paging'] = paging
                data['page'] = page
                data['records'] = page.object_list
                data['inscripcion'] = inscripcion
                data['search'] = search if search else ""
                data['historia_notas'] = REGISTRO_HISTORIA_NOTAS
                data['MODELO_EVALUATIVO'] = [MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, EVALUACION_ITS]
                return render(request ,"inscripciones/historicobs.html" ,  data)
            elif action=='addclase':
                data['title'] = 'Adicionar Clase a Horario'
                grupopractica = GrupoPractica.objects.get(pk=request.GET['nivel'])
                practica = Practica.objects.get(pk=request.GET['practica'])
                turnopractica = TurnoPractica.objects.get(pk=request.GET['turno'])
                data['practica'] = practica
                data['turnopractica'] = turnopractica
                data['nivel'] = grupopractica
                data['dia'] = request.GET['dia']
                if 'materia' in request.GET:
                    form = ClaseConduccionForm(initial={'practica': Practica.objects.get(pk=request.GET['materia'])})
                else:
                    form = ClaseConduccionForm(instance=ClaseConduccion(practica=data['practica'], turnopractica=data['turnopractica'], dia=request.GET['dia']))

                form.for_grupopractica(turnopractica,practica)
                data['form'] = form
                return render(request ,"practicasconduc/adicionahorario.html" ,  data)

            elif action=='delclase':
                clase = ClaseConduccion.objects.get(pk=request.GET['id'])
                clasecon = ClaseConduccion.objects.filter(vehiculo = clase.vehiculo, profesor=clase.profesor,practica=clase.practica,turnopractica=clase.turnopractica)
                clasecon.delete()
                return HttpResponseRedirect('/practicasconduc?action=horario&id='+str(clase.practica.grupopracticas.id)+'&practica='+str(clase.practica.id)+'&ret=1')
            elif action=='delalumno':
                alumno = AlumnoPractica.objects.get(pk=request.GET['id'])
                practica=alumno.claseconduccion.practica.id
                alumno.delete()
                return HttpResponseRedirect('/practicasconduc?action=consulta&practica='+str(practica))

            elif action=='editclase':
                data['title'] = 'Editar Clase de Horario'
                clase = ClaseConduccion.objects.get(pk=request.GET['id'])
                practica = Practica.objects.get(pk=clase.practica.id)
                data['clase'] = clase
                form = ClaseConduccionForm(initial=model_to_dict(clase))
                form.for_grupopracticaedit(clase.turnopractica,practica)
                data['form'] = form
                data['nivel'] = clase.practica.grupopracticas
                return render(request ,"practicasconduc/editar_clase.html" ,  data)

            elif action=='editvehiculo':
                data['title'] = 'Editar Clase de Horario'
                clase = ClaseConduccion.objects.get(pk=request.GET['id'])
                practica = Practica.objects.get(pk=clase.practica.id)
                data['clase'] = clase
                form = ClaseConduccionForm(initial=model_to_dict(clase))
                form.for_vehiculo(clase.turnopractica,practica)
                data['form'] = form
                data['nivel'] = clase.practica.grupopracticas
                return render(request ,"practicasconduc/editar_vehiculo.html" ,  data)


            else:
                return HttpResponseRedirect("/practicasconduc")
        else:
            if CENTRO_EXTERNO==True:
                nivel = Nivel.objects.filter()[:1].get()
                return HttpResponseRedirect("/niveles?action=materias&id="+str(nivel.id))

            else:
                if MODELO_EVALUACION==EVALUACION_TES:
                    # Mostrar panel TES
                    data['periodo'] = Periodo.objects.get(pk=request.session['periodo'].id)
                    data['coordinaciones'] = Coordinacion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct()
                    data['niveles'] = GrupoPractica.objects.filter(periodo=data['periodo']).order_by('paralelo')
                    # data['carreras'] = Carrera.objects.filter(grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct().order_by('nombre')
                    return render(request ,"niveles/libres/nivelesbs.html" ,  data)
                else:
                    data['periodo'] = Periodo.objects.get(pk=request.session['periodo'].id)
                    data['sedes'] = Sede.objects.all()
                    data['carreras'] = Carrera.objects.filter(grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct().order_by('nombre')
                    # data['niveles'] = Nivel.objects.filter(periodo=data['periodo'],carrera__in=data['carreras']).order_by('paralelo')
                    data['niveles'] = GrupoPractica.objects.filter(periodo=data['periodo'],carrera__in=data['carreras']).order_by('carrera')
                    return render(request ,"practicasconduc/nivelesbs.html" ,  data)
