from django.urls import re_path

from firmaec.views import solicitudes

urlpatterns = [
    re_path(r'^solicitudes$', solicitudes.view, name='firmaec_solicitudes_view'),
]

