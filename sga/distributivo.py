from datetime import datetime, timedelta
import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
import unicodedata
from decorators import secure_module
from settings import UTILIZA_COORDINACIONES
from sga.commonviews import addUserData, total_efectivo_dia, cantidad_facturas_dia, cantidad_cheques_dia, total_cheque_dia, cantidad_tarjetas_dia, total_tarjeta_dia, cantidad_depositos_dia, total_deposito_dia, cantidad_transferencias_dia, total_transferencia_dia, cantidad_notasdecredito_dia, total_notadecredito_dia, total_dia, total_matriculados, cantidad_facturas_total_fechas, total_pagos_rango_fechas, facturas_total_fecha, pagos_total_fecha, cantidad_total_deudores, valor_total_deudores, valor_total_porcobrar, cantidad_total_porcobrar, valor_total_creditos, cantidad_total_creditos, total_matriculados_hombres, total_matriculados_mujeres, cantidad_matriculados_discapacidad, cantidad_matriculados_beca, matriculados_menor_30, matriculados_31_40, matriculados_41_50, matriculados_51_60, matriculados_mayor_61, cantidad_total_deudores_retirados, cantidad_total_deudores_inactivos, cantidad_total_deudores_activos, valor_total_deudores_retirados, valor_total_deudores_inactivos, valor_total_deudores_activos, cantidad_total_creditos_retirados, valor_total_creditos_activos, cantidad_total_creditos_inactivos, valor_total_creditos_inactivos, valor_total_creditos_retirados, cantidad_total_creditos_activos, valor_total_porcobrar_retirados, valor_total_porcobrar_inactivos, valor_total_porcobrar_activos, cantidad_total_porcobrar_retirados, cantidad_total_porcobrar_inactivos, cantidad_total_porcobrar_activos
from sga.models import SesionCaja, Coordinacion, Carrera, Inscripcion, Provincia, Canton, Sexo, Sesion, Aula, Sede,ProfesorMateria,Profesor, AulaAdministra, Persona


def convertir_fecha(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2])).date()

def elimina_tildes(s):
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='colchartsesion':
            hoy = datetime.today().date()
            #Sesiones del dia con algun valor final
            data = {"results": [{"id": x.id, "caja":x.caja.nombre, "efectivo":x.total_efectivo_sesion(), "cheque":x.total_cheque_sesion(),
                                 "tarjeta":x.total_tarjeta_sesion(),"deposito":x.total_deposito_sesion(),"transf":x.total_transferencia_sesion(),
                                 "ncredito":x.total_notadecredito_sesion()} for x in SesionCaja.objects.filter(fecha=hoy).order_by('caja__nombre') if x.total_sesion()]}
            return HttpResponse(json.dumps(data), content_type="application/json")
        elif action=='colchartsesionfecha':
            fecha = convertir_fecha(request.POST['fecha'])
            #Sesiones del dia con algun valor final
            data = {"results": [{"id": x.id, "caja":x.caja.nombre, "efectivo":x.total_efectivo_sesion(), "cheque":x.total_cheque_sesion(),
                                 "tarjeta":x.total_tarjeta_sesion(),"deposito":x.total_deposito_sesion(),"transf":x.total_transferencia_sesion(),
                                 "ncredito":x.total_notadecredito_sesion()} for x in SesionCaja.objects.filter(fecha=fecha).order_by('caja__nombre') if x.total_sesion()]}
            return HttpResponse(json.dumps(data), content_type="application/json")


    else:
        data = {'title': 'Estadisticas y Graficos'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='aulas':
                data['title'] = 'Distributivo de aulas segun fecha'
                fecha = convertir_fecha(request.GET['fecha'])
                dia = fecha.weekday() + 1
                # sesion = Sesion.objects.get(pk=request.GET['sesion'])
                sede = Sede.objects.get(pk=request.GET['sede'])

                data['dia'] = dia
                data['fecha'] = fecha
                data['sede'] = sede


                aulas = sede.aulas()   #Obtener todas las aulas de una sede

                lista_aulas = []
                data["aulaadmin"] = False
                for aula in aulas.exclude(tipo__id=9):
                    try :
                        ocupada = aula.ocupada_fecha(fecha,  dia)
                        clases = aula.clases_fecha(fecha,  dia)
                        if ocupada:
                            for clase in clases:
                                if ProfesorMateria.objects.filter(materia=clase.materia).exists():
                                    p=''
                                    for profesor in ProfesorMateria.objects.filter(materia=clase.materia):
                                        if profesor.profesor_aux == None:
                                            prof = profesor.profesor
                                        else:
                                            prof = Profesor.objects.get(pk=profesor.profesor_aux)

                                        p = str (p) + ' - ' +  str(elimina_tildes(prof.persona.nombre_completo()))
                                        if clase.materia.aula_libre():

                                            lista_aulas.append((aula, ocupada, clase,p))
                        else:
                            lista_aulas.append((aula, ocupada, clases))
                    except Exception as ex:
                        pass

                for aula in aulas.filter(tipo__id=9):
                    try :
                        data["aulaadmin"] = True
                        fechaaud = datetime(int(request.GET['fecha'].split("-")[2]),int(request.GET['fecha'].split("-")[1]),int(request.GET['fecha'].split("-")[0]),0,0,0)
                        ocupada = False
                        if AulaAdministra.objects.filter(aula=aula, fecha=fechaaud).exists():
                            ocupada = True
                        aulaad=""
                        if ocupada:
                            for aulaad in AulaAdministra.objects.filter(aula=aula, fecha=fechaaud):
                                persona = Persona.objects.filter(usuario=aulaad.user)[:1].get()

                                p = str(elimina_tildes(persona.nombre_completo()))

                                lista_aulas.append((aula, ocupada, aulaad,p))
                        else:
                            lista_aulas.append((aula, ocupada, aulaad))
                    except Exception as ex:
                        pass

                data['lista_aulas'] = lista_aulas
                return render(request ,"distributivo/aulas.html" ,  data)

            return HttpResponseRedirect("/distributivo")
        else:
            data = {'title': 'Distributivo de Aulas'}
            addUserData(request,data)
            data['hoy'] = datetime.now().today()
            data['sesiones'] = Sesion.objects.all()
            data['sedes'] = Sede.objects.filter(solobodega=False)
            return render(request ,"distributivo/fechas.html" ,  data)

