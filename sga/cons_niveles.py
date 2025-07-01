# -*- coding: latin-1 -*-
from datetime import datetime, timedelta
import json
import os
import time
import xlwt

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models.aggregates import Max
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
import requests
from settings import CALCULA_FECHA_FIN_MATERIA, REPORTE_CRONOGRAMA_MATERIAS, TIPO_PERIODO_PROPEDEUTICO, NIVEL_MALLA_CERO, EVALUACION_ITB, MODELO_EVALUACION, \
    GENERAR_RUBROS_PAGO, EVALUACION_TES, EVALUACION_IGAD, EMAIL_ACTIVE,CENTRO_EXTERNO,DEFAULT_PASSWORD,MODULO_FINANZAS_ACTIVO,ASIGNATURA_PRACTICA_CONDUCCION,\
    INSCRIPCION_CONDUCCION,NOTA_PARA_APROBAR,ASIST_PARA_APROBAR,MEDIA_ROOT
from sga.commonviews import addUserData, ip_client_address
from sga.forms import Inscripcion, NivelForm, NivelFormEdit, MateriaForm, NivelPropedeuticoForm, ProfesorMateriaFormAdd, PagoNivelForm, PagoNivelEditForm, AsignarMateriaGrupoForm, NivelLibreForm, AdicionarOtroRubroForm, MateriaFormCext, ObservacionAbrirMateriaForm
from sga.models import Periodo, Sede, Carrera, Nivel, Materia, Feriado, NivelMalla, Malla, AsignaturaNivelacionCarrera, \
     ProfesorMateria, MateriaAsignada, RecordAcademico, HistoricoRecordAcademico, HistoriaNivelesDeInscripcion, HistoricoNotasITB, \
     Clase, PagoNivel, Rubro, RubroMatricula, RubroCuota, Leccion, AsistenciaLeccion, Coordinacion, NivelLibreCoordinacion, RubroOtro,\
     Matricula,Profesor,Persona,TipoIncidencia,MateriaNivel,TituloInstitucion
from time import sleep
from sga.pro_cronograma import mail_correoprofe
from sga.reportes import elimina_tildes
def convert_fecha(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2]))

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']

            if action=='fechamatriculaextra':
                fechaex = convert_fecha(request.POST['fechaordinaria']) + timedelta(30)
                return HttpResponse(json.dumps({"result":"ok", "fechamatriculaex": fechaex.strftime("%d-%m-%Y")}),content_type="application/json")

            elif action =='generarexcel':
                try:
                    materia = Materia.objects.filter(pk=request.POST['matid'])[:1].get()
                    profesor=ProfesorMateria.objects.filter(materia=materia)[:1].get()
                    m = 10
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtituloazul = xlwt.easyxf('font: name Times New Roman, colour blue, bold on')
                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m, 'LISTADO DE ASISTENCIAS DE ESTUDIANTES POR MATERIA',titulo2)
                    ws.write(3, 0,'CARRERA: ' +materia.nivel.carrera.nombre , subtitulo)
                    ws.write(4, 0,'GRUPO:   ' +materia.nivel.grupo.nombre, subtitulo)
                    ws.write(5, 0,'NIVEL:   ' +materia.nivel.nivelmalla.nombre, subtitulo)
                    ws.write(6, 0,'DOCENTE: ' +profesor.profesor.persona.nombre_completo(), subtitulo)
                    fila = 8
                    com = 8
                    detalle = 3
                    columna=8
                    c=6
                    ws.write_merge(com,fila,0,4,elimina_tildes(materia.nombre_completo()),subtitulo)
                    ws.write_merge(com,fila,5,5,"DEUDA",subtitulo)
                    ws.write_merge(com,fila,6,7,"TELEFONOS DE CONTACTO",subtitulo)
                    for leccion in materia.lecciones():
                        ws.write(fila,columna,str(leccion.fecha), subtitulo)
                        columna=columna+1
                    com=fila+1
                    fila = fila +1
                    columna=8
                    celular=''
                    convencional=''
                    for mate in MateriaAsignada.objects.filter(materia=materia).distinct('matricula__inscripcion').order_by('matricula__inscripcion__persona__apellido1','matricula__inscripcion__persona__apellido2','matricula__inscripcion__persona__nombres'):
                        #print((mate))
                        try:
                            celular=elimina_tildes(mate.matricula.inscripcion.persona.telefono)
                            convencional=elimina_tildes(mate.matricula.inscripcion.persona.telefono_conv)
                        except Exception as ex:
                            celular=''
                            convencional=''

                        if mate.verifica_ultimas_tres_asistencias():
                            ws.write_merge(com,fila,0,4,elimina_tildes(mate.matricula.inscripcion),subtituloazul)
                            ws.write(fila,5,mate.matricula.inscripcion.adeuda_a_la_fecha(),subtituloazul)
                            ws.write(fila,6,celular+' '+convencional,subtituloazul)
                        else:
                            ws.write_merge(com,fila,0,4,elimina_tildes(mate.matricula.inscripcion),subtitulo)
                            ws.write(fila,5,mate.matricula.inscripcion.adeuda_a_la_fecha(),subtitulo)
                            ws.write(fila,6,celular+' '+convencional)

                        for mat in mate.asistencias():
                            if mat.asistio:
                                if mate.verifica_ultimas_tres_asistencias():
                                    ws.write(fila,columna,str('x'), subtituloazul)
                                else:
                                    ws.write(fila,columna,str('x'), subtitulo3)
                            else:
                                ws.write(fila,columna,'', subtitulo3)
                            columna=columna+1

                        columna=8
                        com=fila+1
                        fila = fila +1

                    columna=8
                    fila = fila +1
                    detalle = detalle + fila
                    ws.write(detalle,0, "Fecha Impresion", subtitulo)
                    ws.write(detalle,1, str(datetime.now()), subtitulo)
                    detalle=detalle+2
                    ws.write(detalle,0, "Usuario", subtitulo)
                    ws.write(detalle,1, str(request.user), subtitulo)

                    nombre ='asistenciasxmateria'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")
                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

            elif action =='generarexcel2':
                try:
                    materia = Materia.objects.filter(pk=request.POST['matid'])[:1].get()
                    asignada=MateriaAsignada.objects.filter(materia=materia)[:1].get()
                    nivel = asignada.matricula.nivel
                    matriculados =materia.asignados_a_esta_materia()
                    m = 8
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Informacion',cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0,0,0,m + 2, tit.nombre , titulo2)
                    ws.write_merge(1,1,0,m + 2, 'DATOS DE ESTUDIANTES ' + nivel.grupo.nombre, titulo2)
                    ws.write_merge(2,2,0,m + 2, elimina_tildes(materia.asignatura.nombre), titulo2)
                    detalle = 4
                    fila = 4

                    for mat in matriculados:
                        #print(mat)
                        identificacion=''
                        emailinst=''
                        email=''

                        if mat.matricula.inscripcion.persona.cedula:
                            identificacion = mat.matricula.inscripcion.persona.cedula
                        else:
                            identificacion = mat.matricula.inscripcion.persona.pasaporte

                        if mat.matricula.inscripcion.persona.emailinst:
                            emailinst=mat.matricula.inscripcion.persona.emailinst
                        else:
                            emailinst=''

                        if mat.matricula.inscripcion.persona.email:
                            email=mat.matricula.inscripcion.persona.email
                        else:
                            email=''

                        ws.write(fila, 0, elimina_tildes(mat.matricula.inscripcion.persona.nombres))
                        ws.write(fila, 1, elimina_tildes(mat.matricula.inscripcion.persona.apellido1) + " " +elimina_tildes(mat.matricula.inscripcion.persona.apellido2) )
                        ws.write(fila, 2, emailinst)
                        ws.write(fila, 3, str(identificacion))
                        ws.write(fila, 4, elimina_tildes(mat.matricula.nivel.carrera.nombre))
                        ws.write(fila, 5, elimina_tildes(mat.matricula.inscripcion.persona.usuario.username))
                        ws.write(fila, 6, email)
                        fila=fila + 1

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 1, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 1, str(request.user), subtitulo)

                    nombre ='datos'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({"result":str(ex)+str(mat.matricula.inscripcion)}), content_type="application/json")

            return HttpResponseRedirect("/cons_niveles")

        else:
            data = {'title': 'Niveles Academicos'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action=='tomandom':
                    data['title'] = 'Tomando la Materia'
                    materia = Materia.objects.get(pk=request.GET['id'])
                    inscripcion = Inscripcion.objects.filter(matricula__materiaasignada__materia=materia)
                    data['materia']= materia
                    data['inscripciones'] = inscripcion
                    data['grupo'] = request.GET['grupo']
                    return render(request ,"niveles/tomandobs.html" ,  data)


                elif action=='materias':
                    data['title'] = 'Materias del Nivel Academico'
                    nivel = Nivel.objects.get(pk=request.GET['id'])
                    data['nivel'] = nivel

                    data['cronogramapagos'] = MODULO_FINANZAS_ACTIVO
                    data['materialibre'] = MODELO_EVALUACION==EVALUACION_TES
                    data['centroexterno'] = CENTRO_EXTERNO

                    if CENTRO_EXTERNO:
                        from ext.models import MateriaExterna
                        materias = nivel.materia_set.filter(cerrado=False).order_by('inicio', 'id')
                        for materia in materias:
                            #if materia.materiaexterna_set.all()[:1].get().exportada:
                            if MateriaExterna.objects.filter(materia=materia).exists():
                                paralelo = {'paralelo': MateriaExterna.objects.filter(materia=materia)[:1].get().codigo }
                                entidad = {'entidad': MateriaExterna.objects.filter(materia=materia)[:1].get().entidad.codigo }
                                cantexport = {'cantexport': MateriaExterna.objects.filter(materia=materia)[:1].get().cantexport }
                            else:
                                paralelo = {'paralelo':''}
                                entidad = {'entidad':''}
                                cantexport = {'cantexport':''}

                            materia.__dict__.update(paralelo)
                            materia.__dict__.update(entidad)
                            materia.__dict__.update(cantexport)
                    else:
                        if INSCRIPCION_CONDUCCION:
                            materias = nivel.materia_set.all().order_by('inicio', 'id').exclude(asignatura__id=ASIGNATURA_PRACTICA_CONDUCCION)
                        else:
                            materias = nivel.materia_set.all().order_by('inicio', 'id')
                    data['materias'] = materias
                    data['materianivel'] = MateriaNivel.objects.filter(nivel=nivel)
                    return render(request ,"cons_niveles/materiasbs.html" ,  data)

                elif action=='pagos':
                    data['title'] = 'Cronograma de Pagos del Nivel Academico'
                    nivel = Nivel.objects.get(pk=request.GET['id'])
                    data['nivel'] = nivel
                    data['pagos'] = nivel.pagonivel_set.all().order_by('tipo')
                    if 'e' in request.GET:
                        data['e'] = request.GET['e']
                    data['editable'] = MODELO_EVALUACION!=EVALUACION_TES
                    return render(request ,"cons_niveles/pagosbs.html" ,  data)

                else:
                    return HttpResponseRedirect("/niveles")
            else:
                if CENTRO_EXTERNO==True:
                    nivel = Nivel.objects.filter()[:1].get()
                    return HttpResponseRedirect("/niveles?action=materias&id="+str(nivel.id))

                else:
                    addUserData(request, data)
                    if MODELO_EVALUACION==EVALUACION_TES:
                        # Mostrar panel TES
                        data['periodo'] = Periodo.objects.get(pk=request.session['periodo'].id)
                        data['coordinaciones'] = Coordinacion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct()
                        data['niveles'] = Nivel.objects.filter(periodo=data['periodo'], nivellibrecoordinacion__coordinacion__in=data['coordinaciones']).order_by('paralelo')
                        return render(request ,"niveles/libres/nivelesbs.html" ,  data)
                    else:
                        #OCastillo 10-07-2023 cambio de la presentacion de consulta niveles como en niveles y los grupos de usuarios
                        #jefe asuntos y asuntos tienen las carreras asignadas en grupos responsables de carreras
                        # if not request.user.groups.filter(id__in =(64,65)) :
                        periodo = Periodo.objects.get(pk=request.session['periodo'].id)
                        sedes = Sede.objects.filter(solobodega=False)
                        # data['carreras'] = Carrera.objects.filter(grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct().order_by('nombre').order_by('nombre')
                        carreras = Carrera.objects.filter(grupocoordinadorcarrera__group__in=request.user.groups.all()).distinct().exclude(activo=False).order_by('nombre').order_by('nombre')
                        data['periodo'] = periodo
                        data['carreras'] = carreras
                        niveles = Nivel.objects.filter(periodo=data['periodo'],carrera__in=data['carreras']).order_by('paralelo')
                        data['sedes'] = sedes
                        data['select_carreras'] = carreras
                        data['niveles'] = niveles
                        data['user']=request.user

                        if 'c' in request.GET:
                            if request.GET['c'] != 0:
                                data['carreras'] = carreras.filter(pk=request.GET['c'])
                                data['niveles'] = niveles.filter(carrera__in=data['carreras'])
                                niveless = niveles.filter(carrera__in=data['carreras'])
                                data['sedes'] = sedes
                                if sedes.filter(id__in=niveless.values('sede')).exists():
                                    data['sede'] = sedes.filter(id__in=niveless.values('sede'))[:1].get()
                                data['filtro'] = True

                        if 'n' in request.GET:
                            data['niveles'] = ''
                            data['filtro'] = True
                            nivel = Nivel.objects.filter(pk=request.GET['n'])
                            if nivel.filter(periodo=periodo).exists():
                                data['carreras'] = carreras.filter(id__in=nivel.values('carrera'))
                                data['niveles'] = nivel
                                data['sedes'] = sedes.filter(id__in=nivel.values('sede'))
                                data['sede'] = sedes.filter(id__in=nivel.values('sede'))[:1].get()
                            else:
                                data['carreras'] = None
                                print('NO EXISTE NIVEL EN ESTE PERIODO')
                                data['msj']='EL NIVEL '+nivel[:1].get().paralelo+' SE ENCUENTRA EN EL PERIODO: '+nivel[:1].get().periodo.nombre

                        # else:
                        #     #OCastillo 19-05-2022 para que dpto asuntos pueda ver todas las carreras
                        #     data['periodo'] = Periodo.objects.get(pk=request.session['periodo'].id)
                        #     data['sedes'] = Sede.objects.filter(solobodega=False)
                        #     data['carreras'] = Carrera.objects.filter(carrera=True).distinct().exclude(activo=False).order_by('nombre').order_by('nombre')
                        #     data['niveles'] = Nivel.objects.filter(periodo=data['periodo'],carrera__in=data['carreras']).order_by('paralelo')
                        #     data['select_carreras'] = carreras
                        #     data['niveles'] = niveles
                        #     data['user']=request.user

                        return render(request ,"cons_niveles/nivelesbs.html" ,  data)

    except:
        return HttpResponseRedirect('/niveles')
