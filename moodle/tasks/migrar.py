import threading
import sys
from django.db import transaction


class CreacionMasiva(threading.Thread):

    def __init__(self, request, eNivel):
        self.request = request
        self.eNivel = eNivel
        threading.Thread.__init__(self)

    def run(self):
        from sga.models import Materia
        from moodle.functions import crear_curso_eva
        request, eNivel = self.request, self.eNivel
        try:
            eMaterias = Materia.objects.filter(cerrado=False, nivel=eNivel)
            total = eMaterias.values("id").count()
            contador = 0
            for eMateria in eMaterias:
                contador += 1
                print(f"({total}/{contador}) Procesando....")
                if not eMateria.id_moodle_course:
                    with transaction.atomic():
                        try:
                            crear_curso_eva(eMateria)
                            print(f"({total}/{contador}) Curso: {eMateria.__str__()}, creado en EVA")
                        except Exception as _ex:
                            transaction.set_rollback(True)
                            print(u"Error al crear el curso en EVA: %s" % _ex.__str__())
            print(f"Finalizado....")
        except Exception as ex:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            print(f'{ex.__str__()}')
