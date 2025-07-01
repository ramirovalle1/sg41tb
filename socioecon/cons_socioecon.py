from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
import xlwt
from settings import CARRERAS_ID_EXCLUIDAS_INEC, PERSONA_CUBRE_GASTOS_OTROS_ID, INSTITUCION, INSTITUTO_ITB, INSTITUTO_ITF, INSTITUTO_BUCK, SEXO_FEMENINO, SEXO_MASCULINO, MEDIA_ROOT, MEDIA_URL
from sga.commonviews import addUserData
from sga.models import Inscripcion, Carrera, Coordinacion, Sexo,Canton, EstudioInscripcion, TituloInstitucion, elimina_tildes
from socioecon.forms import SustentoHogarForm, TipoHogarForm, PersonaCubreGastoForm, NivelEstudioForm, OcupacionJefeHogarForm, TipoViviendaForm, MaterialParedForm, MaterialPisoForm, CantidadBannoDuchaForm, TipoServicioHigienicoForm, CantidadTVColorHogarForm, CantidadVehiculoHogarForm, CantidadCelularHogarForm, OcupacionEstudianteForm, IngresosEstudianteForm, BonoFmlaEstudianteForm
from socioecon.models import InscripcionFichaSocioeconomica, GrupoSocioEconomico, cantidad_gruposocioeconomico_carrera, cantidad_gruposocioeconomico_coordinacion, NivelEstudio, cantidad_nivel_educacion_jefehogar_carrera, \
     cantidad_nivel_educacion_jefehogar_coordinacion, TipoHogar, cantidad_tipo_hogar_carrera, cantidad_tipo_hogar_coordinacion, cantidad_SIdependientes_carrera, \
     cantidad_NOdependientes_carrera, cantidad_SIdependientes_coordinacion, cantidad_NOdependientes_coordinacion, cantidad_SIcabezasf_carrera, cantidad_NOcabezasf_carrera, \
     cantidad_SIcabezasf_coordinacion, cantidad_NOcabezasf_coordinacion, cantidad_SIcabezasf_carrera_mujer, cantidad_SIcabezasf_carrera_hombre, cantidad_beca_SIcabezasf_carrera, \
     cantidad_total_madres_solteras, cantidad_total_beca_madres_solteras,cantidad_mayorcinco_miembros_carrera,cantidad_total_casados_xsexo, cantidad_total_estudiantes_congreso, cantidad_total_mujeresxedad, cantidad_total_menoresedad, cantidad_gruposocioeconomico_carrera_general

# Metodo para obtener el Ip desde donde se conectan los usuarios
def ip_client_address(request):
    try:
        # case server externo
        client_address = request.META['HTTP_X_FORWARDED_FOR']
    except:
        # case localhost o 127.0.0.1
        client_address = request.META['REMOTE_ADDR']
    return client_address

def ficha_socioeconomica_estudiante(inscripcion):
    if not inscripcion.inscripcionfichasocioeconomica_set.exists():
        fichasocioecon = InscripcionFichaSocioeconomica(inscripcion=inscripcion)
        fichasocioecon.save()
    else:
        fichasocioecon = inscripcion.inscripcionfichasocioeconomica_set.all()[:1].get()
    return fichasocioecon


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    if request.method=='POST':
        action = request.POST['action']

    else:
        data = {'title': 'Ficha SocioEconomica del Estudiante'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']

            if action=='segmento':
                data = {'title': 'Consulta de Alumnos - Nivel Socioeconomico'}
                inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                ficha = ficha_socioeconomica_estudiante(inscripcion)
                data['inscripcion'] = inscripcion
                data['ficha'] = ficha
                return render(request ,"cons_socioecon/segmento.html" ,  data)

            elif action=='search':
                search = request.GET['term']
                data = {}

                if ' ' in search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)>1:
                        data['inscripciones'] = Inscripcion.objects.filter(Q(persona__apellido1__icontains=ss[0]) & Q(persona__apellido2__icontains=ss[1]),persona__usuario__is_active=True).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                    else:
                        data['inscripciones'] = Inscripcion.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search), persona__usuario__is_active=True).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                else:
                    data['inscripciones'] = Inscripcion.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search), persona__usuario__is_active=True).order_by('persona__apellido1','persona__apellido2','persona__nombres')

                return render(request ,"cons_socioecon/selector.html" ,  data)

            #ACCIONES PARA TABLAS Y GRAFICAS
            elif action=='tbl_gpo_carrera':
                if 'anno' in request.GET:
                    anno = request.GET['anno']

                    inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                    fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                    #Conformacion de Tabla de grupos socioeconomicos por carreras
                    data = {'title': 'Grupos Socioeconomicos por carreras'}

                    addUserData(request,data)
                    carreras = [c for c in Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('coordinacion') if c.mat_carrera(inicio,fin)]
                    lista_carreras_grupos = []
                    for c in carreras:
                        lista_grupos = []
                        for grupo in GrupoSocioEconomico.objects.all():
                            lista_grupos.append(cantidad_gruposocioeconomico_carrera(grupo, c,inicio,fin))
                        lista_carreras_grupos.append((c.alias, lista_grupos))

                    data['carreras'] = carreras
                    data['anno'] = anno
                    data['lista_carreras_grupos'] = lista_carreras_grupos
                    data['grupos_socioeconomicos'] = GrupoSocioEconomico.objects.all()
                    return render(request ,"cons_socioecon/tbl_gpo_carrera.html" ,  data)
                else:
                    data = {'title': 'Grupos Socioeconomicos por carreras en general'}

                    addUserData(request,data)
                    carreras = [c for c in Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('coordinacion')]
                    lista_carreras_grupos = []
                    for c in carreras:
                        lista_grupos = []
                        for grupo in GrupoSocioEconomico.objects.all():
                            lista_grupos.append(cantidad_gruposocioeconomico_carrera_general(grupo, c))
                        lista_carreras_grupos.append((c.alias, lista_grupos))
                    data['carreras'] = carreras

                    data['lista_carreras_grupos'] = lista_carreras_grupos
                    data['grupos_socioeconomicos'] = GrupoSocioEconomico.objects.all()
                    return render(request ,"cons_socioecon/tbl_gpo_carrera.html" ,  data)

            elif action=='generar_excel':
                print('ok')

                titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                titulo.font.height = 20*11
                titulo2.font.height = 20*11
                subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                subtitulo.font.height = 20*10
                style1 = xlwt.easyxf('',num_format_str='DD-MMM-YY')
                wb = xlwt.Workbook()

                num_hoja=1
                hoja='tblgpocarreras'
                ws = wb.add_sheet(hoja,cell_overwrite_ok=True)
                tit = TituloInstitucion.objects.all()[:1].get()
                ws.write_merge(0, 0,0,6, tit.nombre , titulo2)
                ws.write_merge(1, 1,0,6, 'TABLA - NIVEL SOCIOECONOMICO POR CARRERAS ', titulo2)
                ws.write_merge(2, 3,0,0, ' CARRERAS ', titulo2)
                ws.write_merge(2, 2,1,5, ' GRUPO SOCIECONOMICO ', titulo2)
                grupeco=1
                for grupo in GrupoSocioEconomico.objects.all():
                    ws.write(3,grupeco,grupo.codigo)
                    grupeco=grupeco +1
                grupcar=4

                for carrera in Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('coordinacion'):
                    ws.write(grupcar,0, elimina_tildes(carrera.nombre))
                    grupsoc=1
                    for grupo in GrupoSocioEconomico.objects.all():
                        cantidad=(cantidad_gruposocioeconomico_carrera_general(grupo, carrera))
                        ws.write(grupcar,grupsoc,cantidad)
                        grupsoc=grupsoc+1
                    grupcar=grupcar+1
                grupeco=1
                ws.write(grupcar,0,'TOTAL',titulo2)
                for socioeco in GrupoSocioEconomico.objects.all():
                    ws.write(grupcar,grupeco,socioeco.cantidad_total_estudiantes_general())
                    grupeco=grupeco+1
                detalle = grupcar + 3
                ws.write(detalle,0, "Fecha Impresion", subtitulo)
                ws.write(detalle,1, str(datetime.now()), subtitulo)
                detalle=detalle+2
                ws.write(detalle,0, "Usuario", subtitulo)
                ws.write(detalle,1, str(request.user), subtitulo)

                nombre ='tblgpocarrera'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                return HttpResponseRedirect("/media"+'/reporteexcel/'+nombre)
                # return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                # for c in Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('coordinacion'):
                #     for grupo in GrupoSocioEconomico.objects.all():






            elif action=='tbl_gpo_coordinacion':
                anno = request.GET['anno']
                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                #Conformacion de Tabla de grupos socioeconomicos por coordinaciones
                data = {'title': 'Grupos Socioeconomicos por coordinaciones'}
                addUserData(request,data)
                coordinaciones = Coordinacion.objects.all().order_by('id')
                lista_coordinaciones_grupos = []
                for c in coordinaciones:
                    lista_grupos = []
                    for grupo in GrupoSocioEconomico.objects.all():
                        lista_grupos.append(cantidad_gruposocioeconomico_coordinacion(grupo, c,inicio,fin))

                    lista_coordinaciones_grupos.append((c.nombre, lista_grupos))

                data['coordinaciones'] = coordinaciones
                data['anno'] = anno
                data['lista_coordinaciones_grupos'] = lista_coordinaciones_grupos
                data['grupos_socioeconomicos'] = GrupoSocioEconomico.objects.all()
                return render(request ,"cons_socioecon/tbl_gpo_coord.html" ,  data)

            elif action=='graph_nivelescolar_jefehogar':
                anno = request.GET['anno']
                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                #Conformacion de Graficos para mostrar el nivel escolar de los jefes de hogar
                data = {'title': 'Niveles de Escolaridad Jefes de Hogar'}
                addUserData(request,data)
                coordinaciones = Coordinacion.objects.all().order_by('id')
                carreras = [c for c in Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('coordinacion') if c.mat_carrera(inicio,fin)]
                lista_carreras_nivel_estudios = []
                for c in carreras:
                    lista_nivelestudio = []
                    for nivel in NivelEstudio.objects.all():
                        lista_nivelestudio.append(cantidad_nivel_educacion_jefehogar_carrera(nivel, c,inicio,fin))
                    lista_carreras_nivel_estudios.append((c.alias, lista_nivelestudio))

                data['anno'] = anno
                data['carreras'] = carreras
                data['lista_carreras_nivel_estudios'] = lista_carreras_nivel_estudios

                lista_coordinaciones_nivel_estudios = []
                for c in coordinaciones:
                    lista_nivelestudio = []
                    for nivel in NivelEstudio.objects.all():
                        lista_nivelestudio.append(cantidad_nivel_educacion_jefehogar_coordinacion(nivel, c,inicio,fin))

                    lista_coordinaciones_nivel_estudios.append((c.nombre, lista_nivelestudio))

                data['coordinaciones'] = coordinaciones
                data['lista_coordinaciones_nivel_estudios'] = lista_coordinaciones_nivel_estudios

                data['niveles_estudios'] = NivelEstudio.objects.all()
                return render(request ,"cons_socioecon/graf_nivelescolar_jefeh.html" ,  data)

            elif action=='graph_tipohogar':
                #Conformacion de Graficos para mostrar el tipo de hogar de estudiantes
                data = {'title': 'Tipos de hogares de lo estudiantes'}
                addUserData(request,data)
                anno = request.GET['anno']
                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                coordinaciones = Coordinacion.objects.all().order_by('id')
                carreras = [c for c in Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('coordinacion') if c.mat_carrera(inicio,fin)]
                lista_carreras_tipo_hogar = []
                for c in carreras:
                    lista_tipohogar = []
                    for th in TipoHogar.objects.all():
                        lista_tipohogar.append(cantidad_tipo_hogar_carrera(th, c,inicio,fin))
                    lista_carreras_tipo_hogar.append((c.alias, lista_tipohogar))

                data['carreras'] = carreras
                data['lista_carreras_tipo_hogar'] = lista_carreras_tipo_hogar

                lista_coordinaciones_tipo_hogar = []
                for c in coordinaciones:
                    lista_tipohogar = []
                    for th in TipoHogar.objects.all():
                        lista_tipohogar.append(cantidad_tipo_hogar_coordinacion(th, c,inicio,fin))

                    lista_coordinaciones_tipo_hogar.append((c.nombre, lista_tipohogar))

                data['coordinaciones'] = coordinaciones
                data['anno'] = anno
                data['lista_coordinaciones_tipo_hogar'] = lista_coordinaciones_tipo_hogar

                data['tipos_hogares'] = TipoHogar.objects.all()
                return render(request ,"cons_socioecon/graf_tipohogar.html" ,  data)

            elif action=='graph_dependencia_carrera':
                #Conformacion de Graficos de Dependencias Economicas por Carreras
                data = {'title': 'Dependencia Economica por carreras'}
                addUserData(request,data)
                anno = request.GET['anno']
                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                carreras = [c for c in Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('coordinacion') if c.mat_carrera(inicio,fin)]
                lista_carreras_dependencia = []
                for c in carreras:
                    lista_carreras_dependencia.append((c.alias, cantidad_SIdependientes_carrera(c,inicio,fin), cantidad_NOdependientes_carrera(c,inicio,fin), c.id))
                data['lista_carreras_dependencia'] = lista_carreras_dependencia
                data['anno'] = anno
                return render(request ,"cons_socioecon/graf_depend_carrera.html" ,  data)

            elif action=='graph_dependencia_coordinacion':
                #Conformacion de Graficos de Dependencias Economicas por Coordinaciones
                data = {'title': 'Dependencia Economica por coordinaciones'}
                addUserData(request,data)
                anno = request.GET['anno']
                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                coordinaciones = Coordinacion.objects.all().order_by('id')
                lista_coordinaciones_dependencia = []
                for c in coordinaciones:
                    lista_coordinaciones_dependencia.append((c.nombre, cantidad_SIdependientes_coordinacion(c,inicio,fin), cantidad_NOdependientes_coordinacion(c,inicio,fin), c.id))
                data['lista_coordinaciones_dependencia'] = lista_coordinaciones_dependencia
                data['anno'] = anno
                return render(request ,"cons_socioecon/graf_depend_coord.html" ,  data)

            elif action=='graph_cabezaf_carrera':
                #Conformacion de Graficos de Cabezas de Familia por Carreras
                data = {'title': 'Estudiantes cabezas de familias por carreras'}
                addUserData(request,data)
                anno = request.GET['anno']
                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                carreras = [c for c in Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('coordinacion') if c.mat_carrera(inicio,fin)]
                lista_carreras_cabezasf = []
                for c in carreras:
                    lista_carreras_cabezasf.append((c.alias, cantidad_SIcabezasf_carrera(c,inicio,fin), cantidad_NOcabezasf_carrera(c,inicio,fin), c.id))
                data['lista_carreras_cabezasf'] = lista_carreras_cabezasf
                data['anno'] = anno
                return render(request ,"cons_socioecon/graf_cabezas_carrera.html" ,  data)
            elif action=='graph_cabezaf_beca_carrera':
                #Conformacion de Graficos de Becados Cabezas de Familia por Carreras
                data = {'title': 'Estudiantes Becados cabezas de familias por carreras y Sexo'}
                addUserData(request,data)
                anno = request.GET['anno']
                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                carreras = [c for c in Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('coordinacion') if c.mat_carrera_beca(inicio,fin)]
                lista_carreras_cabezasf_beca = []
                for c in carreras:
                    if cantidad_beca_SIcabezasf_carrera(c,inicio,fin,SEXO_FEMENINO)> 0 or cantidad_beca_SIcabezasf_carrera(c,inicio,fin,SEXO_MASCULINO)>0:
                        lista_carreras_cabezasf_beca.append((c.alias, cantidad_beca_SIcabezasf_carrera(c,inicio,fin,SEXO_FEMENINO), cantidad_beca_SIcabezasf_carrera(c,inicio,fin,SEXO_MASCULINO), c.id))
                data['lista_carreras_cabezasf_beca'] = lista_carreras_cabezasf_beca
                data['anno'] = anno
                return render(request ,"cons_socioecon/graf_cabezas_beca_carrera_sexo.html" ,  data)
            elif action=='graph_madre_soltera':
                #Conformacion de Graficos de Becados Cabezas de Familia por Carreras
                data = {'title': 'Estudiantes Madres Solteras'}
                addUserData(request,data)
                anno = request.GET['anno']
                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                carreras = [c for c in Carrera.objects.all().order_by('nombre').exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('nombre') if c.madres_solteras(anno)>0]
                data['carreras']=carreras
                data['anno']=anno
                data['cantidad_total_madres_solteras']=cantidad_total_madres_solteras(inicio,fin)
                return render(request ,"cons_socioecon/graf_madre_solteras.html" ,  data)

            elif action=='graph_beca_madre_soltera':
                #Conformacion de Graficos de Becados Cabezas de Familia por Carreras
                data = {'title': 'Estudiantes Becadas Madres Solteras'}
                addUserData(request,data)
                anno = request.GET['anno']
                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                carreras = [c for c in Carrera.objects.all().order_by('nombre').exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('nombre') if c.madres_solteras_beca(anno)>0]
                data['carreras']=carreras
                data['anno']=anno
                data['cantidad_total_beca_madres_solteras']=cantidad_total_beca_madres_solteras(inicio,fin)
                return render(request ,"cons_socioecon/graf_beca_madre_solteras.html" ,  data)


            elif action=='graph_cabezaf_carrera_sexo':
                #Conformacion de Graficos de Cabezas de Familia por Carreras
                data = {'title': 'Estudiantes cabezas de familias por carreras y Sexo'}
                addUserData(request,data)
                anno = request.GET['anno']
                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                carreras = [c for c in Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('coordinacion') if c.mat_carrera(inicio,fin)]
                lista_carreras_cabezasf = []
                for c in carreras:
                    lista_carreras_cabezasf.append((c.alias, cantidad_SIcabezasf_carrera_mujer(c,inicio,fin), cantidad_SIcabezasf_carrera_hombre(c,inicio,fin), c.id))
                data['lista_carreras_cabezasf'] = lista_carreras_cabezasf
                data['anno'] = anno
                return render(request ,"cons_socioecon/graf_cabezas_carrera_sexo.html" ,  data)

            elif action=='graph_cabezaf_coordinacion':
                #Conformacion de Graficos de Cabezas de Familia por Coordinaciones
                data = {'title': 'Estudiantes cabezas de familias por coordinaciones'}
                addUserData(request,data)
                anno = request.GET['anno']
                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                coordinaciones = Coordinacion.objects.all().order_by('id')
                lista_coordinaciones_cabezasf = []
                for c in coordinaciones:
                    lista_coordinaciones_cabezasf.append((c.nombre, cantidad_SIcabezasf_coordinacion(c,inicio,fin), cantidad_NOcabezasf_coordinacion(c,inicio,fin), c.id))
                data['lista_coordinaciones_cabezasf'] = lista_coordinaciones_cabezasf
                data['anno'] = anno
                return render(request ,"cons_socioecon/graf_cabezas_coord.html" ,  data)

            elif action=='verficha':
                inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                ficha = ficha_socioeconomica_estudiante(inscripcion)
                data['inscripcion'] = inscripcion
                data['ficha'] = ficha

                #Sustentos del hogar Form
                data['form_sustento'] = SustentoHogarForm(initial={'ingresomensual': 0.00})
                #Tipos de Hogares Form
                data['form_tipohogar'] = TipoHogarForm()
                #Quien cubre el gasto del estudiante Form
                data['form_personacubregasto'] = PersonaCubreGastoForm()
                data['personacubregasto_OTROS_ID'] = PERSONA_CUBRE_GASTOS_OTROS_ID
                #Nivel de Educacion de Jefe de Hogar Form
                data['form_niveljefehogar'] = NivelEstudioForm()
                #Ocupacion de Jefe de Hogar Form
                data['form_ocupacionjefehogar'] = OcupacionJefeHogarForm()

                 #Tipo de Vivienda Form
                data['form_tipovivienda'] = TipoViviendaForm()
                #Material predomina en Paredes Form
                data['form_materialpared'] = MaterialParedForm()
                #Material predomina en Piso Form
                data['form_materialpiso'] = MaterialPisoForm()
                #Cantidad de Banos con Duchas Form
                data['form_cantbannoducha'] = CantidadBannoDuchaForm()
                #Tipo de Servicio Higienico Form
                data['form_tiposervhig'] = TipoServicioHigienicoForm()
                #Cantidad de TV a color Form
                data['form_canttvcolor'] = CantidadTVColorHogarForm()
                #Cantidad de Vehiculos Form
                data['form_cantvehiculos'] = CantidadVehiculoHogarForm()
                #Cantidad de Celulares Form
                data['form_cantcelulares'] = CantidadCelularHogarForm()

                data['form_ocupacionestudiante'] = OcupacionEstudianteForm()
                data['form_ingresosestudiante'] = IngresosEstudianteForm()
                data['form_bonofmlaestudiante'] = BonoFmlaEstudianteForm()

                #Logo de cada institucion que tenga el modulo de ficha socioeconomica
                data['INSTITUTO'] = [INSTITUCION, INSTITUTO_ITB, INSTITUTO_ITF, INSTITUTO_BUCK]

                # #Obtain client ip address
                # client_address = ip_client_address(request)
                #
                # # Log de FICHA SOCIOECONOMICA
                # LogEntry.objects.log_action(
                #     user_id         = request.user.pk,
                #     content_type_id = ContentType.objects.get_for_model(ficha).pk,
                #     object_id       = ficha.id,
                #     object_repr     = force_str(ficha),
                #     action_flag     = ADDITION,
                #     change_message  = 'Consulta Ficha Socioecon (' + client_address + ')'  )

                return render(request ,"alu_socioecon/ficha.html" ,  data)

            #OCU 31-01-2019 solicitado por bienestar
            elif action=='tbl_mayornumero_integrantes_carrera':
                anno = request.GET['anno']
                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                data = {'title': 'Estudiantes con familia mayor a Cinco Miembros por Tipo de Hogares y Carreras'}

                addUserData(request,data)
                carreras = [c for c in Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('coordinacion') if c.mat_carrera(inicio,fin)]
                lista_carreras_grupos = []
                for c in carreras:
                    lista_thogar = []
                    for thogar in TipoHogar.objects.all():
                        lista_thogar.append(cantidad_mayorcinco_miembros_carrera(thogar, c,inicio,fin))
                    lista_carreras_grupos.append((c.alias, lista_thogar))

                data['carreras'] = carreras
                data['anno'] = anno
                data['lista_carreras_grupos'] = lista_carreras_grupos
                data['grupos_tipohogar'] = TipoHogar.objects.all()
                return render(request ,"cons_socioecon/tbl_tipohogar_carrera.html" ,  data)

            elif action=='tbl_casadosmenoreigual25_carrera':
                anno = request.GET['anno']
                edad = request.GET['edad']
                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                data = {'title': 'Estudiantes Casados Menores a '+ edad +  'por Carreras'}
                addUserData(request,data)
                carreras = [c for c in Carrera.objects.all().exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('coordinacion') if c.mat_carrera(inicio,fin)]
                lista_carreras_grupos = []
                listamujeres_carrera=[]

                for c in carreras:
                    lista_sexo = []
                    listamujeres_carrera.append((c.alias,cantidad_total_mujeresxedad(c,edad,inicio,fin)))

                    for s in Sexo.objects.all().order_by('nombre'):
                        lista_sexo.append(cantidad_total_casados_xsexo(c,s,edad,inicio,fin))
                    lista_carreras_grupos.append((c.alias, lista_sexo))

                data['carreras'] = carreras
                data['anno'] = anno
                data['edad'] = edad
                data['lista_carreras_grupos'] = lista_carreras_grupos
                data['lista_mujeres_carreras'] = listamujeres_carrera
                data['grupos_sexo'] = Sexo.objects.all().order_by('nombre')
                return render(request ,"cons_socioecon/tbl_casados_menosveintiseis_carrera.html" ,  data)

            elif action=='tbl_estudiantes_congreso':
                anno = request.GET['anno']
                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                data = {'title': 'Estudiantes que Participaron en Congreso'}

                addUserData(request,data)
                carreras = [c for c in Carrera.objects.all().order_by('nombre').exclude(id__in=CARRERAS_ID_EXCLUIDAS_INEC).order_by('coordinacion') if c.congreso_xanio(anno)]
                data['total_estudiantes_congreso']= cantidad_total_estudiantes_congreso(inicio,fin)
                data['carreras'] = carreras
                data['anno'] = anno
                return render(request ,"cons_socioecon/tbl_estudiantes_congreso.html" ,  data)

            elif action=='tbl_estudiante_clasificacion':
                 dato = request.GET['anno']
                 # Total de estudiantes por Hombres y  Mujeres
                 listaCantiHM = []
                 listaCantiHM.append(('Mujeres',Inscripcion.objects.filter(fecha__year=dato,persona__sexo__id=SEXO_FEMENINO).count()))
                 listaCantiHM.append(('Hombres',Inscripcion.objects.filter(fecha__year=dato,persona__sexo__id=SEXO_MASCULINO).count()))
                 data['listadoHM']=listaCantiHM

                 #Total de estudiantes con discapacidad
                 listaDiscapHMT = []
                 listaDiscapHMT.append(('Mujeres',Inscripcion.objects.filter(fecha__year=dato,persona__sexo__id=SEXO_FEMENINO,tienediscapacidad=True).count()))
                 listaDiscapHMT.append(('Hombres',Inscripcion.objects.filter(fecha__year=dato,persona__sexo__id=SEXO_MASCULINO,tienediscapacidad=True).count()))
                 data['listaDiscapHMT']=listaDiscapHMT

                 #Total de estudiantes con tercera Edad
                 listaTeceraHMT = []
                 lMTercera = [x for x in Inscripcion.objects.filter(fecha__year=dato,persona__sexo__id=SEXO_FEMENINO) if x.persona.edad()>=65]
                 lHTercera = [x for x in Inscripcion.objects.filter(fecha__year=dato,persona__sexo__id=SEXO_MASCULINO) if x.persona.edad()>=65]
                 listaTeceraHMT.append(('Mujeres',len(lMTercera)))
                 listaTeceraHMT.append(('Hombres',len(lHTercera)))
                 data['listaTeceraHMT']=listaTeceraHMT

                 data['periodo']=dato

                 #Estudiantes Menores de Edad
                 inicio=datetime.strptime('01-01-'+str(dato[2:4]), '%d-%m-%y').date()
                 fin=datetime.strptime('31-12-'+str(dato[2:4]), '%d-%m-%y').date()
                 listaMenoresEdad = []
                 for s in Sexo.objects.all().order_by('nombre'):
                        listaMenoresEdad.append((s.nombre,(cantidad_total_menoresedad(s,inicio,fin))))
                 data['listaMenoresEdad']=listaMenoresEdad

            return render(request ,"cons_socioecon/tbl_estudiante_clasificacion.html" ,  data)
        else:
            if 'alumno' in request.GET:
                inscripcion = Inscripcion.objects.get(pk=request.GET['alumno'])
                ficha = ficha_socioeconomica_estudiante(inscripcion)
                data['inscripcion'] = inscripcion
                data['ficha'] = ficha

            return render(request ,"cons_socioecon/consultas.html" ,  data)



