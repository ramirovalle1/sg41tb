from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from core.my_model import ModelBase


def upload_repository_directory_path(instance, filename):
    ahora = datetime.now()
    return 'repositorio/{0}/{1}/{2}/{3}/{4}'.format(
        instance.get_tipo_display().lower(),
        ahora.year,
        f'{ahora.month:02d}',
        f'{ahora.day:02d}',
        filename
    )


class Repositorio(ModelBase):
    class Tipos(models.IntegerChoices):
        NINGUNO = 0, "Ninguno"
        PDF = 1, "PDF"
        IMAGE = 2, "Imagen"
        WORD = 3, "Word"
        EXCEL = 4, "Excel"

    nombre = models.CharField(verbose_name='Nombre', max_length=350)
    tipo = models.IntegerField(choices=Tipos.choices, default=Tipos.NINGUNO, verbose_name='Tipo')
    archivo = models.FileField(upload_to=upload_repository_directory_path, verbose_name='Archivo')

    def __str__(self):
        return self.nombre
