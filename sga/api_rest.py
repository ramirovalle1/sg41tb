from django.http import JsonResponse

from sga.api_content.alumnos.aluFacturasElectronicas import aluFacturasElectronicas
from sga.api_content.alumnos.aluMaterias import aluMaterias
from sga.api_content.alumnos.aluCronograma import aluCronograma
from sga.api_content.alumnos.aluHorarios import aluHorarios
from sga.api_content.alumnos.aluMalla import aluMalla
from sga.api_content.alumnos.ficha_medica import ficha_medica

from sga.api_content.alumnos.finanzas import alu_finanzas
from sga.api_content.general.account import cuenta
from sga.api_content.general.inscripcion import inscripcion
from sga.api_content.login import apiLogin
from sga.api_content.modelos.cantones import cantones
from sga.api_content.modelos.parroquias import parroquias
from sga.api_content.modelos.provincias import provincias
from sga.api_content.panel import apiPanel


def view(request):
    try:
        print(request.GET)
        if request.method == 'GET':
            action = request.GET.get('action')
            action_map = {
                'login': apiLogin,
                'panel': apiPanel,
                'inscripcion': inscripcion,
                'provincias': provincias,
                'cantones': cantones,
                'parroquias': parroquias,
                'account': cuenta,
                'alu_finanzas': alu_finanzas,
                'alu_medical': ficha_medica,
                'alu_cronograma': aluCronograma,
                'alu_malla': aluMalla,
                'alu_horarios': aluHorarios,
                'alu_materias': aluMaterias,
                'alu_facturacion_electronica': aluFacturasElectronicas
            }

            if action in action_map:
                func = action_map[action]

                #Recolectamos todos los parámetros dinámicamente de request.GET
                params = request.GET.dict()
                #Quitamos el 'action' ya que no es un argumento para las funciones
                params.pop('action', None)

                #Llamamos a la función correspondiente con los parámetros dinámicos
                return func(request, **params)

            else:
                return JsonResponse({"error": "Accion no valida"}, status=400)
        else:
            return JsonResponse({"error": "Metodo no permitido"}, status=405)
    except Exception as e:
        print(e)
        return JsonResponse({"error": "Error interno del servidor"}, status=500)


def decimal_format(num):
    return "{:.2f}".format(num)
