# -*- coding: utf-8 -*-
import sys
from decimal import Decimal
from settings import DEBUG
from datetime import datetime
from django.contrib.auth.models import User
from django.db import connections, transaction
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from hashlib import md5


class UserAuth(models.Model):
    user = models.OneToOneField(User, db_index=True, on_delete=models.CASCADE)
    username = models.CharField(default='', max_length=100, verbose_name=u'Nombre de usuario', db_index=True, unique=True)
    password = models.CharField(default='', max_length=1000, verbose_name=u"Contraseña")
    first_name = models.CharField(default='', max_length=250, verbose_name=u"Nombres")
    last_name = models.CharField(default='', max_length=250, verbose_name=u"Apellidos")
    email = models.CharField(default='', max_length=200, verbose_name=u"Correo Institucional")
    city = models.CharField(default='Guayaquil', max_length=150, verbose_name=u"Ciudad")

    def __str__(self):
        return u'%s - %s %s' % (self.username, self.first_name, self.last_name)

    class Meta:
        verbose_name = u"Moodle Usuario"
        verbose_name_plural = u"Moodle Usuarios"
        ordering = ['username']

    def get_person(self):
        from sga.models import Persona
        try:
            return Persona.objects.get(usuario=self.user)
        except ObjectDoesNotExist:
            return None

    def set_data(self):
        ePerson = self.get_person()
        if self.user and ePerson:
            self.username = self.user.username
            self.first_name = ePerson.get_nombres()
            self.last_name = ePerson.get_apellidos()
            self.email = ePerson.emailinst.strip()
            self.city = ePerson.ciudad if ePerson.ciudad else "Guayaquil"

    def check_data(self):
        isUpdate = False
        ePerson = self.get_person()
        first_name = ePerson.get_nombres()
        last_name = ePerson.get_apellidos()
        email = ePerson.emailinst.strip()
        city = ePerson.ciudad if ePerson.ciudad else "Guayaquil"
        if not self.username == self.user.username:
            isUpdate = True
            self.username = self.user.username
        if not self.first_name == first_name:
            isUpdate = True
            self.first_name = first_name
        if not self.last_name == last_name:
            isUpdate = True
            self.last_name = last_name
        if not self.email == email:
            isUpdate = True
            self.email = email
        if not self.city == city:
            isUpdate = True
            self.city = city
        return isUpdate

    def set_password(self, pwd):
        self.password = md5(pwd.encode("utf-8")).hexdigest()

    def check_password(self, pwd):
        return self.password == md5(pwd.encode("utf-8")).hexdigest()

    def save(self, *args, **kwargs):
        super(UserAuth, self).save(*args, **kwargs)


class EvaVirtual(models.Model):
    class TypesConnections(models.TextChoices):
        NINGUNA = 'ninguna', "NINGUNA"
        EVA_1 = 'moodle_eva_1', "EVA 1"
        EVA_2 = 'moodle_eva_2', "EVA 2"
        EVA_3 = 'moodle_eva_3', "EVA 3"

    type_connection = models.CharField(choices=TypesConnections.choices, max_length=50, default=TypesConnections.NINGUNA, verbose_name=u'Tipo de conexión')
    name = models.CharField(default='', max_length=150, verbose_name=u'Nombre', unique=True)
    name_key = models.CharField(default='', max_length=50, verbose_name=u'Nombre Corto', unique=True)
    url = models.CharField(blank=True, null=True, max_length=500, verbose_name=u'URL')
    prefix_db = models.CharField(blank=True, null=True, max_length=50, verbose_name=u'Prefijo de BD')
    token = models.CharField(blank=True, null=True, max_length=500, verbose_name=u'Token')
    role_teacher = models.IntegerField(blank=True, null=True, verbose_name=u'Rol de Profesor')
    role_student = models.IntegerField(blank=True, null=True, verbose_name=u'Rol de Estudiante')
    category_id = models.IntegerField(blank=True, null=True, verbose_name=u'ID Categoria')
    is_active = models.BooleanField(default=True, verbose_name=u'¿Está activo?')

    def __str__(self):
        name = self.name_key if self.name_key else self.name
        if self.url:
            name = "%s (%s)" % (name, self.url)
        return u'%s' % name.strip()

    class Meta:
        verbose_name = u"EVA Virtual"
        verbose_name_plural = u"EVAs virtuales"
        ordering = ['name']
        # unique_together = ('',)

    def has_web_service_data(self):
        return False if not self.url or not self.prefix_db or not self.token or not self.role_student or not self.role_teacher or not self.category_id else True

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.name_key = self.name_key.strip()
        super(EvaVirtual, self).save(*args, **kwargs)
