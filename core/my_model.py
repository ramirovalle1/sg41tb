# from cgi import escape
from datetime import datetime
from django.utils.text import capfirst
from django.contrib.admin.utils import NestedObjects, quote
from django.utils.encoding import force_str
from django.db import transaction, router, models


ADMINISTRADOR_ID = 1


class ModelBase(models.Model):
    """ Modelo base para todos los modelos del proyecto """
    from django.contrib.auth.models import User
    es_activo = models.BooleanField(default=True)
    usuario_creacion = models.ForeignKey(User, related_name='+', on_delete=models.SET_NULL, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario_modificacion = models.ForeignKey(User, related_name='+', on_delete=models.SET_NULL, blank=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user_ = None
        if len(args):
            user_ = args[0].user.id
        for key, value in kwargs.items():
            if 'user_id' == key:
                user_ = value
        if self.id:
            self.usuario_modificacion_id = user_ if user_ else ADMINISTRADOR_ID
            self.fecha_modificacion = datetime.now()
        else:
            self.usuario_creacion_id = user_ if user_ else ADMINISTRADOR_ID
            self.fecha_creacion = datetime.now()
        models.Model.save(self)

    class Meta:
        abstract = True
