from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import render
from django.utils.encoding import force_str
from settings import CARRERAS_ID_EXCLUIDAS_INEC, PERSONA_CUBRE_GASTOS_OTROS_ID, INSTITUCION, INSTITUTO_ITB, INSTITUTO_ITF, INSTITUTO_BUCK
from sga.commonviews import addUserData
from sga.models import Inscripcion, Carrera, Coordinacion, cantidad_inscritos, total_beneficiados, registro_edades, cantidad_adm, total_beneficiados_adm,total_beneficiados_condu,total_beneficiados_otros,cantidad_condu,cantidad_otros
from socioecon.forms import SustentoHogarForm, TipoHogarForm, PersonaCubreGastoForm, NivelEstudioForm, OcupacionJefeHogarForm, TipoViviendaForm, MaterialParedForm, MaterialPisoForm, CantidadBannoDuchaForm, TipoServicioHigienicoForm, CantidadTVColorHogarForm, CantidadVehiculoHogarForm, CantidadCelularHogarForm
from socioecon.models import InscripcionFichaSocioeconomica, GrupoSocioEconomico, cantidad_gruposocioeconomico_carrera, cantidad_gruposocioeconomico_coordinacion, NivelEstudio, cantidad_nivel_educacion_jefehogar_carrera, cantidad_nivel_educacion_jefehogar_coordinacion, TipoHogar, cantidad_tipo_hogar_carrera, cantidad_tipo_hogar_coordinacion, cantidad_SIdependientes_carrera, cantidad_NOdependientes_carrera, cantidad_SIdependientes_coordinacion, cantidad_NOdependientes_coordinacion, cantidad_SIcabezasf_carrera, cantidad_NOcabezasf_carrera, cantidad_SIcabezasf_coordinacion, cantidad_NOcabezasf_coordinacion, cantidad_SIcabezasf_carrera_mujer, cantidad_SIcabezasf_carrera_hombre

# Metodo para obtener el Ip desde donde se conectan los usuarios

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    if request.method=='POST':
        action = request.POST['action']

    else:
        data = {'title': 'Estadisticas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']



            #ACCIONES PARA TABLAS Y GRAFICAS
            if action=='registro':
                anno = request.GET['anno']

                inicio=datetime.strptime('01-01-'+str(anno[2:4]), '%d-%m-%y').date()
                fin=datetime.strptime('31-12-'+str(anno[2:4]), '%d-%m-%y').date()
                #Conformacion de Tabla de grupos socioeconomicos por carreras
                data = {'title': 'Estudiantes Beneficiados'}
                addUserData(request,data)


                carreras = [c for c in Carrera.objects.all()]
                lista_carreras_grupos = []
                for c in carreras:
                    lista_grupos = []
                    if cantidad_inscritos(c,inicio,fin):
                        lista_grupos.append(cantidad_inscritos(c,inicio,fin))
                        lista_carreras_grupos.append((c.alias, lista_grupos))

                lista_grupos = []
                lista_grupos.append(cantidad_adm(inicio,fin))
                lista_carreras_grupos.append(('ADMINISTRATIVOS', lista_grupos))

                lista_grupos = []
                lista_grupos.append(cantidad_condu(inicio,fin))
                lista_carreras_grupos.append(('CONDUCCION', lista_grupos))

                lista_grupos = []
                lista_grupos.append(cantidad_otros(inicio,fin))
                lista_carreras_grupos.append(('OTROS', lista_grupos))

                data['carreras'] = carreras
                data['anno'] = anno
                data['lista_carreras_grupos'] = lista_carreras_grupos
                # data['total_b'] = total_beneficiados(inicio,fin) + total_beneficiados_adm(inicio,fin)
                data['total_b'] = total_beneficiados(inicio,fin) + total_beneficiados_adm(inicio,fin)+total_beneficiados_condu(inicio,fin)+total_beneficiados_otros(inicio,fin)
                edades = ['0','1','2','3']
                total_edades = []
                for c in edades:
                    lista_edades = []
                    lista_edades.append(len(registro_edades(inicio,fin,int(c))))
                    total_edades.append((c, lista_edades))

                data['carreras'] = edades
                data['anno'] = anno
                data['total_edades'] = total_edades
                return render(request ,"guarderia/registroestadistica.html" ,  data)


        else:
            return render(request ,"guarderia/consultas.html" ,  data)



