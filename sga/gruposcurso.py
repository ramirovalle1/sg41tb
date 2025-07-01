# -*- coding: latin-1 -*-
from datetime import datetime, timedelta
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
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
from settings import CALCULA_FECHA_FIN_MATERIA, REPORTE_CRONOGRAMA_MATERIAS, TIPO_PERIODO_PROPEDEUTICO, NIVEL_MALLA_CERO, EVALUACION_ITB, MODELO_EVALUACION, GENERAR_RUBROS_PAGO, EVALUACION_TES, EVALUACION_IGAD, ASIGNATURA_PRACTICA_CONDUCCION, RUBRO_TIPO_CURSOS
from settings import CALCULA_FECHA_FIN_MATERIA, CENTRO_EXTERNO, REPORTE_CRONOGRAMA_MATERIAS, TIPO_PERIODO_PROPEDEUTICO, NIVEL_MALLA_CERO,\
    EVALUACION_ITB, MODELO_EVALUACION, GENERAR_RUBROS_PAGO, EVALUACION_TES,PORCIENTO_NOTA1,PORCIENTO_NOTA2,PORCIENTO_NOTA3,\
    PORCIENTO_NOTA4, PORCIENTO_NOTA5, PORCIENTO_RECUPERACION,NOTA_ESTADO_APROBADO,REGISTRO_HISTORIA_NOTAS,MODELO_EVALUACION, EVALUACION_IAVQ, EVALUACION_ITB, EVALUACION_ITS
from sga.commonviews import addUserData, ip_client_address
from sga.forms import Inscripcion, NivelForm, NivelFormEdit, MateriaForm, NivelPropedeuticoForm, ProfesorMateriaFormAdd, PagoNivelForm, PagoNivelEditForm, AsignarMateriaGrupoForm, NivelLibreForm, AdicionarOtroRubroForm, MateriaFormCext, ObservacionAbrirMateriaForm, GrupoPracticaForm, PracticaForm, GrupoPracticaFormEdit, ClaseConduccionForm, HistoricoNotasPracticaForm, MateriaCursoForm, PagoCursoForm, GrupoCursoForm, AsignarGrupoMasivoForm
from sga.models import Periodo, Sede, Carrera, Nivel, Materia, Feriado, NivelMalla, Malla, AsignaturaNivelacionCarrera, ProfesorMateria, MateriaAsignada,\
    RecordAcademico, HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, HistoricoNotasITB, Clase, PagoNivel, Rubro, RubroMatricula, RubroCuota, Leccion,\
    AsistenciaLeccion, Coordinacion, NivelLibreCoordinacion, RubroOtro, GrupoPractica, Practica,TurnoPractica,ClaseConduccion,Vehiculo,Profesor, \
    AlumnoPractica,Asignatura,TipoEstado, HistoricoNotasPractica, GrupoCurso, MateriaCurso, PagosCurso, InscripcionMateria, DetallePagos, Materia, TipoOtroRubro
from time import sleep
from settings import MODULO_FINANZAS_ACTIVO,INSTITUTO_ITB,API_URL_ITB
from ext.models import *

def convert_fecha(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2]))
def inscribir(grupo,i):
    pagocurso = PagosCurso.objects.filter(grupocurso=grupo)
    hoy = datetime.now().date()
    for p in pagocurso:
        detallepagos = DetallePagos(inscripcion = i,
                                    grupocurso=p.grupocurso,
                                    pagocurso=p)
        detallepagos.save()
        if detallepagos.grupocurso.activo:
            detallepagos.activo=True
            detallepagos.save()
            r1 = Rubro( fecha =hoy,
                                        valor = p.valor,
                                        inscripcion = i,
                                        cancelado = False,
                                        fechavence = p.fechavence)
            r1.save()
            r1otro = RubroOtro(rubro=r1,
                               tipo=TipoOtroRubro.objects.get(pk=RUBRO_TIPO_CURSOS),
                               descripcion= p.grupocurso.nombre + " - " + p.nombre)
            r1otro.save()
            detallepagos.rubro = r1
            detallepagos.save()

    if detallepagos.grupocurso.activo:
        for m in MateriaCurso.objects.filter(grupocurso=detallepagos.grupocurso):
                    imateria = InscripcionMateria(inscripcion=i,
                                                  materia=m,
                                                  fecha=hoy)
                    imateria.save()
@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='addpagos':
            grupocurso = GrupoCurso.objects.get(pk=request.POST['id'])
            f = PagoCursoForm(request.POST)
            if f.is_valid():
                pagocurso = PagosCurso(nombre=f.cleaned_data['nombre'],grupocurso=grupocurso, fechavence=f.cleaned_data['fechavence'],valor=f.cleaned_data['valor'])
                pagocurso.save()

                client_address = ip_client_address(request)

                # Log de ADICIONAR MATERIA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(pagocurso).pk,
                    object_id       = pagocurso.id,
                    object_repr     = force_str(pagocurso),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Pago de Curso (' + client_address + ')' )

                return HttpResponseRedirect("/gruposcurso?action=pagos&id="+str(grupocurso.id))
            else:
                 return HttpResponseRedirect("/gruposcurso")


        elif action=='deletemateria':
            materiacurso = MateriaCurso.objects.get(pk=request.POST['id'])

            client_address = ip_client_address(request)

                # Log de ADICIONAR MATERIA
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(materiacurso).pk,
                object_id       = materiacurso.id,
                object_repr     = force_str(materiacurso),
                action_flag     = DELETION,
                change_message  = 'Eliminada Materia de Curso (' + client_address + ')' )

            materiacurso.delete()
            data={}
            grupocurso=materiacurso.grupocurso
            return HttpResponseRedirect("/gruposcurso?action=cronograma&id="+str(grupocurso.id))

        elif action=='delcurso':
            grupocurso = GrupoCurso.objects.get(pk=request.POST['id'])

            client_address = ip_client_address(request)

                # Log de ADICIONAR MATERIA
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(grupocurso).pk,
                object_id       = grupocurso.id,
                object_repr     = force_str(grupocurso),
                action_flag     = DELETION,
                change_message  = 'Eliminado Curso (' + client_address + ')' )

            grupocurso.delete()

            return HttpResponseRedirect("/gruposcurso")

        elif action=='delpago':
            pagocurso = PagosCurso.objects.get(pk=request.POST['id'])

            client_address = ip_client_address(request)

                # Log de ADICIONAR MATERIA
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(pagocurso).pk,
                object_id       = pagocurso.id,
                object_repr     = force_str(pagocurso),
                action_flag     = DELETION,
                change_message  = 'Eliminado Pago de grupo ' + pagocurso.grupocurso.nombre +' (' + client_address + ')' )

            pagocurso.delete()

            return HttpResponseRedirect("/gruposcurso")

        elif action=='editmateria':
            materiacurso= MateriaCurso.objects.get(pk=request.POST['id'])

            f = MateriaCursoForm(request.POST)
            if f.is_valid():
                materiacurso.asignatura= f.cleaned_data['asignatura']
                materiacurso.inicio = f.cleaned_data['inicio']
                materiacurso.fin = f.cleaned_data['fin']
                materiacurso.instructor = f.cleaned_data['instructor']
                materiacurso.horas = f.cleaned_data['horas']
                materiacurso.grupo= f.cleaned_data['grupo']
                materiacurso.save()

                client_address = ip_client_address(request)

                # Log de ADICIONAR MATERIA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(materiacurso).pk,
                    object_id       = materiacurso.id,
                    object_repr     = force_str(materiacurso),
                    action_flag     = CHANGE,
                    change_message  = 'Editada Materia de Curso (' + client_address + ')' )
                data={}
                grupocurso=materiacurso.grupocurso
                return HttpResponseRedirect("/gruposcurso?action=cronograma&id="+str(grupocurso.id))

            else:
                return HttpResponseRedirect('/gruposcurso')



        elif action=='editpagos':
                pagocurso = PagosCurso.objects.get(pk=request.POST['id'])
                grupocurso = pagocurso.grupocurso
                f = PagoCursoForm(request.POST)
                if f.is_valid():
                    pagocurso.fechavence=f.cleaned_data['fechavence']
                    pagocurso.valor=f.cleaned_data['valor']
                    pagocurso.nombre=f.cleaned_data['nombre']
                    pagocurso.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR PAGOS NIVEL
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(pagocurso).pk,
                        object_id       = pagocurso.id,
                        object_repr     = force_str(pagocurso),
                        action_flag     = CHANGE,
                        change_message  = 'Modificado Cronograma Pago Curso (' + client_address + ')' )

                    return HttpResponseRedirect("/gruposcurso?action=pagos&id="+str(grupocurso.id))
                else:
                     return HttpResponseRedirect("/gruposcurso")
        elif action=='addcurso':
            f = GrupoCursoForm(request.POST)
            if f.is_valid():
                grupocurso = GrupoCurso(nombre = f.cleaned_data['nombre'],
                                        numeropagos=f.cleaned_data['numeropagos'],
                                        activo=f.cleaned_data['activo'])
                grupocurso.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de EDITAR HORARIO CLASE
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(grupocurso).pk,
                    object_id       = grupocurso.id,
                    object_repr     = force_str(grupocurso),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Curso (' + client_address + ')'  )

                return HttpResponseRedirect("/gruposcurso")
            else:
                return HttpResponseRedirect("/gruposcurso")

        elif action=='asignarcurso':
             materia = Materia.objects.get(pk=request.POST['materia'])
             inscripcion = Inscripcion.objects.filter(matricula__materiaasignada__materia=materia)
             f = AsignarGrupoMasivoForm(request.POST)
             if f.is_valid():
                 for i in inscripcion:
                     if not DetallePagos.objects.filter(inscripcion=i,grupocurso=f.cleaned_data['grupo']).exists():
                         inscribir( f.cleaned_data['grupo'],i)

                 return HttpResponseRedirect("/inscripcionescurso")




        elif action=='addmodulo':
            data={}
            grupocurso = GrupoCurso.objects.get(pk=request.POST['idgrupo'])
            f = MateriaCursoForm(request.POST)
            if f.is_valid():
                materiacurso = MateriaCurso(grupocurso=grupocurso,
                                            asignatura=f.cleaned_data['asignatura'],
                                            inicio = f.cleaned_data['inicio'],
                                            fin = f.cleaned_data['fin'],
                                            instructor=f.cleaned_data['instructor'],
                                            grupo=f.cleaned_data['grupo'],
                                            horas = f.cleaned_data['horas'])
                materiacurso.save()

                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de ADICIONAR MATERIA
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(materiacurso).pk,
                    object_id       = materiacurso.id,
                    object_repr     = force_str(materiacurso),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionada Materia a Curso  ' + grupocurso.nombre + '(' + client_address + ')' )

                return HttpResponseRedirect("/gruposcurso?action=cronograma&id="+str(grupocurso.id))

            else:
                return HttpResponseRedirect('/gruposcurso')


        elif action=='editcurso':
            grupocurso = GrupoCurso.objects.get(pk=request.POST['id'])
            f = GrupoCursoForm(request.POST)
            pc=0
            if f.is_valid():
                if PagosCurso.objects.filter(grupocurso=grupocurso).exists():
                    pc = PagosCurso.objects.filter(grupocurso=grupocurso).count()

                if (int(f.cleaned_data['numeropagos']) < pc ):
                    return HttpResponseRedirect("/gruposcurso?action=editcurso&id="+request.POST['id']+"&error=1")
                else:
                    grupocurso.nombre = f.cleaned_data['nombre']
                    grupocurso.numeropagos = f.cleaned_data['numeropagos']
                    grupocurso.activo = f.cleaned_data['activo']
                    grupocurso.save()
                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de ADICIONAR HISTORICO
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(grupocurso).pk,
                        object_id       = grupocurso.id,
                        object_repr     = force_str(grupocurso),
                        action_flag     = ADDITION,
                        change_message  = 'Editado Grupo (' + client_address + ')' )
                    # return HttpResponseRedirect("/practicasconduc?action=consulta&practica="+str(practica.id))
                    return HttpResponseRedirect("/gruposcurso")

        elif action=='verificanumero':
                result = {}
                mc = 0
                pc = 0
                if GrupoCurso.objects.filter(pk=request.POST['grupo']).exists():
                   grupocurso = GrupoCurso.objects.filter(pk=request.POST['grupo'])[:1].get()
                   if PagosCurso.objects.filter(grupocurso=grupocurso).exists():
                       pc = PagosCurso.objects.filter(grupocurso=grupocurso).count()
                       if  MateriaCurso.objects.filter(grupocurso=grupocurso).exists():
                           mc = MateriaCurso.objects.filter(grupocurso=grupocurso).count()
                   if (int(request.POST['numero']) < pc ):
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                   else:
                       return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")

                else :
                    result['result']  = "bad"
                return HttpResponse(json.dumps(result),content_type="application/json")

        return HttpResponseRedirect("/grupocurso")
    else:
        data = {'title': 'Cursos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='cronograma':
                data['title'] = 'Cronograma de Curso'
                if MateriaCurso.objects.filter(grupocurso__id=request.GET['id']).exists():
                    data['cronograma'] = MateriaCurso.objects.filter(grupocurso__id=request.GET['id'])
                data['grupo']=GrupoCurso.objects.get(pk=request.GET['id'])
                return render(request ,"gruposcurso/cronogramacurso.html" ,  data)

            elif action=='editmateria':
                data['title'] = 'Editar Materia'
                materiacurso = MateriaCurso.objects.get(pk=request.GET['id'])
                initial = model_to_dict(materiacurso)
                data['form'] = MateriaCursoForm(initial=initial)
                data['materiacurso'] = materiacurso
                return render(request ,"gruposcurso/editar_modulo.html" ,  data)
            elif action=='delmateria':
                data['title'] = 'Borrar Materia'
                materiacurso = MateriaCurso.objects.get(pk=request.GET['id'])
                data['materiacurso'] = materiacurso
                return render(request ,"gruposcurso/borrarbs.html" ,  data)

            elif action=='delcurso':
                data['title'] = 'Borrar Curso'
                grupocurso = GrupoCurso.objects.get(pk=request.GET['id'])
                data['grupocurso'] = grupocurso
                return render(request ,"gruposcurso/borrarcurso.html" ,  data)


            elif action=='addmodulo':
                data['title'] = 'Adicionar Curso'
                data['grupo'] = GrupoCurso.objects.get(pk=request.GET['id'])
                data['form'] = MateriaCursoForm()
                fecha = datetime.now()
                data['form']= MateriaCursoForm(initial={'inicio':fecha,'fin':fecha})
                data['action'] = 'addmodulo'
                return render(request ,"gruposcurso/adicionar_modulo.html" ,  data)
            elif action=='pagos':
                data['title'] = 'Cronograma de Pagos'
                grupocurso = GrupoCurso.objects.get(pk=request.GET['id'])
                data['grupocurso'] = grupocurso
                if PagosCurso.objects.filter(grupocurso=grupocurso).exists():
                    pagos = PagosCurso.objects.filter(grupocurso=grupocurso)
                    data['pagos'] = pagos
                return render(request ,"gruposcurso/pagos.html" ,  data)
            elif action=='actualizar':
                if DetallePagos.objects.filter(pagocurso__id=request.GET['id']).exists():
                    dpagos = DetallePagos.objects.filter(pagocurso__id=request.GET['id'])
                    for p in dpagos:
                        if Rubro.objects.filter(pk=p.rubro.id,cancelado=False).exists():
                            r = Rubro.objects.get(pk=p.rubro.id)
                            r.valor=p.pagocurso.valor
                            r.fechavence = p.pagocurso.fechavence
                            r.save()

                    return HttpResponseRedirect("/gruposcurso?action=pagos&id="+str(p.grupocurso.id))

            elif action=='agregarvalores':
            #OC junio-2018 para cargar los valores a las finanzas de los estudiantes importados
                matc=''
                grupocurso=''
                inscripmat=''
                if MateriaCurso.objects.filter(grupocurso__id=request.GET['id']).exists():
                    matc=MateriaCurso.objects.filter(grupocurso__id=request.GET['id'])

                if GrupoCurso.objects.filter(pk=request.GET['id']).exists():
                   grupocurso = GrupoCurso.objects.filter(pk=request.GET['id'])[:1].get()

                if InscripcionMateria.objects.filter(materia=matc).exists():
                    inscripmat = InscripcionMateria.objects.filter(materia=matc).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2','inscripcion__persona__nombres')

                for i in inscripmat:
                    pagocurso = PagosCurso.objects.get(pk=request.GET['pid'], grupocurso=grupocurso)
                    if not DetallePagos.objects.filter(inscripcion=i.inscripcion,grupocurso=grupocurso,pagocurso=pagocurso).exists():
                        hoy = datetime.now().date()
                        detallepagos = DetallePagos(inscripcion = i.inscripcion,
                                                    grupocurso=pagocurso.grupocurso,
                                                    pagocurso=pagocurso)
                        detallepagos.save()
                        if detallepagos.grupocurso.activo:
                            detallepagos.activo=True
                            detallepagos.save()
                            r1 = Rubro( fecha =hoy,
                                                        valor = pagocurso.valor,
                                                        inscripcion = i.inscripcion,
                                                        cancelado = False,
                                                        fechavence = pagocurso.fechavence)
                            r1.save()
                            r1otro = RubroOtro(rubro=r1,
                                               tipo=TipoOtroRubro.objects.get(pk=RUBRO_TIPO_CURSOS),
                                               descripcion= pagocurso.grupocurso.nombre + " - " + pagocurso.nombre)
                            r1otro.save()
                            detallepagos.rubro = r1
                            detallepagos.save()

                return HttpResponseRedirect("/gruposcurso?action=pagos&id="+str(grupocurso.id))



            elif action=='editpagos':
                    data['title'] = 'Editar Cronograma de Pagos '
                    pagocurso = PagosCurso.objects.get(pk=request.GET['id'])
                    data['grupocurso'] = pagocurso.grupocurso
                    data['nombre'] = pagocurso.nombre
                    data['fechavence']=pagocurso.fechavence
                    data['valor']=pagocurso.valor
                    initial = model_to_dict(pagocurso)
                    data['form'] = PagoCursoForm(initial=initial)
                    data['pagocurso'] = pagocurso
                    return render(request ,"gruposcurso/editpagosbs.html" ,  data)

            elif action=='addpagos':
                    data['title'] = 'Adicionar Cronograma de Pagos'
                    grupocurso = GrupoCurso.objects.get(pk=request.GET['id'])
                    data['grupocurso'] = grupocurso
                    fecha = datetime.now()
                    data['form']= PagoCursoForm(initial={'fechavence':fecha})
                    return render(request ,"gruposcurso/addpagosbs.html" ,  data)
            elif action=='addcurso':
                    data['title'] = 'Adicionar Curso'
                    data['form']= GrupoCursoForm()
                    return render(request ,"gruposcurso/addcurso.html" ,  data)
            elif action=='editcurso':
                data['title'] = 'Edicion de Grupo'
                if 'error' in request.GET:
                        data['error'] = request.GET['error']
                grupocurso = GrupoCurso.objects.get(pk=request.GET['id'])
                data['grupocurso'] = grupocurso
                initial = model_to_dict(grupocurso)
                data['form']= GrupoCursoForm(initial=initial)
                return render(request ,"gruposcurso/editcurso.html" ,  data)
            elif action=='delpagos':
                data['title'] = 'Borrar Pagos'
                pagocurso = PagosCurso.objects.get(pk=request.GET['id'])
                data['pagocurso'] = pagocurso
                return render(request ,"gruposcurso/borrarpago.html" ,  data)

            elif action=='asignarcurso':
                    data['title'] = 'Asignacion a Curso'
                    materia = Materia.objects.get(pk=request.GET['id'])
                    data['materia']= materia
                    data['form'] = AsignarGrupoMasivoForm()
                    return render(request ,"gruposcurso/addcurso_grupo.html" ,  data)

            elif action=='delmodulo':
                data['title'] = 'Borrar Modulo'
                materiacurso = InscripcionMateria.objects.get(pk=request.GET['id'])
                m=materiacurso.materia.id
                if InscripcionMateria.objects.filter(inscripcion = materiacurso.inscripcion,materia__grupocurso__id=request.GET['grupo']).count() ==  1  :
                    if DetallePagos.objects.filter(grupocurso = materiacurso.materia.grupocurso,inscripcion=materiacurso.inscripcion).exists():
                        pagos = DetallePagos.objects.filter(grupocurso = materiacurso.materia.grupocurso,inscripcion=materiacurso.inscripcion)
                        for p in pagos:
                            if Rubro.objects.filter(pk=p.rubro.id).exists():
                                rubro = Rubro.objects.filter(pk=p.rubro.id)[:1].get()
                                if rubro.puede_eliminarse():
                                    rotro = RubroOtro.objects.filter(rubro=rubro)[:1].get()
                                    rotro.delete()
                                    rubro.delete()

                client_address = ip_client_address(request)

                # Log de ADICIONAR HISTORICO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(materiacurso).pk,
                    object_id       = materiacurso.id,
                    object_repr     = force_str(materiacurso),
                    action_flag     = ADDITION,
                    change_message  = 'Editado Grupo (' + client_address + ')' )
                materiacurso.delete()
                return HttpResponseRedirect("/gruposcurso?action=verinscritos&id="+str(m))


            elif action=='importar_matriculados':
            #OC junio-2018 para importar estudiantes matriculados del SGA a Buck
                materiacurso= MateriaCurso.objects.get(pk=request.GET['id'])
                datos = requests.get(API_URL_ITB,params={'a': 'impgrupo','grupo': materiacurso.grupo })

                if datos.status_code==200:
                    matriculados = datos.json()

                for d in matriculados:
                    try:
                        if not Persona.objects.filter(cedula=d[3]).exists() and  not  Persona.objects.filter(pasaporte=d[3]).exists():
                                    cedula = ''
                                    pasaporte = ''
                                    if len(d[3])==10:
                                        cedula =d[3]
                                    else:
                                        pasaporte = d[3]
                                    p = Persona(apellido1 =d[0],
                                                apellido2 = d[1],
                                                nombres = d[2],
                                                cedula = cedula,
                                                pasaporte = pasaporte,
                                                telefono = d[4],
                                                telefono_conv = d[5],
                                                email = d[6],
                                                direccion = d[7],
                                                direccion2 = d[8])
                                    p.save()
                                    if pasaporte != '':
                                        p.extranjero=True
                                        p.save()

                        else:
                            if Persona.objects.filter(cedula=d[3]).exists():
                                p = Persona.objects.filter(cedula=d[3])[:1].get()
                            else:
                                p = Persona.objects.filter(pasaporte=d[3])[:1].get()

                        if not Inscripcion.objects.filter(persona=p).exists():
                             inscrip = Inscripcion(persona = p,
                                                   carrera_id = 2,
                                                   modalidad_id = 1,
                                                   sesion_id = 1,
                                                   especialidad_id=1,
                                                   fecha=datetime.now())
                             inscrip.save()
                        else:
                             inscrip = Inscripcion.objects.filter(persona=p)[:1].get()

                        if not InscripcionMateria.objects.filter(inscripcion=inscrip).exists():
                            inscripmateria = InscripcionMateria(inscripcion=inscrip,
                                                                materia=materiacurso,
                                                                fecha = datetime.now())
                            inscripmateria.save()

                    except Exception as ex:
                            return HttpResponseRedirect("/?info=Error al Importar "+str(ex))

                client_address = ip_client_address(request)
                # Log de importacion de materia curso
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(materiacurso).pk,
                    object_id       = materiacurso.id,
                    object_repr     = force_str(materiacurso),
                    action_flag     = ADDITION,
                    change_message  = 'Importacion Realizada (' + client_address + ')')

                return HttpResponseRedirect("/gruposcurso?action=cronograma&id="+str(materiacurso.grupocurso.id))

            if action=='verinscritos':
                data['title'] = 'Inscritos de Modulo'
                if InscripcionMateria.objects.filter(materia__id=request.GET['id']).exists():
                    data['alumnolistas'] = InscripcionMateria.objects.filter(materia__id=request.GET['id']).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    m =InscripcionMateria.objects.filter(materia__id=request.GET['id'])[:1].get()
                    data['grupo']=m.materia.grupocurso

                return render(request ,"gruposcurso/inscritosmateria.html" ,  data)

        else:
                data['carreras'] = Carrera.objects.all().distinct().order_by('nombre')
                # data['niveles'] = Nivel.objects.filter(periodo=data['periodo'],carrera__in=data['carreras']).order_by('paralelo')
                data['grupos'] = GrupoCurso.objects.filter().order_by('id')
                return render(request ,"gruposcurso/gruposcurso.html" ,  data)
