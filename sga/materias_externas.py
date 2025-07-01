#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template.context import RequestContext
from decorators import secure_module
from sga.commonviews import addUserData, ip_client_address
from ext.models import *
from settings import EMAIL_ACTIVE

def calculate_username(persona, variant=1):
    s = persona.nombres.lower().split(' ')
    while '' in s:
        s.remove('')
    if len(s) > 1:
        usernamevariant = s[0][0] + s[1][0] + persona.apellido1.lower()
    else:
        usernamevariant = s[0][0] + persona.apellido1.lower()
    usernamevariant = usernamevariant.replace(' ', '').replace(u'Ñ', 'n').replace(u'ñ', 'n')
    if variant > 1:
        usernamevariant += str(variant)
    import psycopg2
    db = psycopg2.connect("host=10.10.9.45 dbname=sgaonline user=postgres password=Itb$2019")
    cursor = db.cursor()
    cursor.execute("select * from auth_user where username='" + str(usernamevariant) + "'")
    dato = cursor.fetchall()
    # names = [row[0] for row in cursor.fetchall()]
    db.close()
    if len(dato) > 0:
        return calculate_username(persona, variant + 1)
    db = psycopg2.connect("host=10.10.9.45 dbname=conduccion user=postgres password=Itb$2019")
    cursor = db.cursor()
    cursor.execute("select * from auth_user where username='" + str(usernamevariant) + "'")
    dato = cursor.fetchall()
    # names = [row[0] for row in cursor.fetchall()]
    db.close()
    if len(dato) > 0:
        return calculate_username(persona, variant + 1)
    db = psycopg2.connect("host=10.10.9.45 dbname=contable2 user=postgres password=Itb$2019")
    cursor = db.cursor()
    cursor.execute("select * from auth_user where username='" + str(usernamevariant) + "'")
    dato = cursor.fetchall()
    # names = [row[0] for row in cursor.fetchall()]
    db.close()
    if len(dato) > 0:
        return calculate_username(persona, variant + 1)
    db = psycopg2.connect("host=10.10.9.45 dbname=educacontinua user=postgres password=Itb$2019")
    cursor = db.cursor()
    cursor.execute("select * from auth_user where username='" + str(usernamevariant) + "'")
    dato = cursor.fetchall()
    # names = [row[0] for row in cursor.fetchall()]
    db.close()
    if len(dato) > 0:
        return calculate_username(persona, variant + 1)
    if User.objects.filter(username=usernamevariant).count() == 0:
        return usernamevariant
    else:
        return calculate_username(persona, variant + 1)

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'obtenermaterias':
            entidad = EntidadImportacion.objects.get(id=request.POST['entidad'])
            result = entidad.importar_datos()
            client_address = ip_client_address(request)

            # Log de ANULAR FACTURA
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(entidad).pk,
                object_id       = entidad.id,
                object_repr     = force_str(entidad),
                action_flag     = ADDITION,
                change_message  = 'Importacion Realizada (' + client_address + ')')
            return HttpResponse(json.dumps(result),content_type="application/json")
        if action == 'exportarmateria':
            materia = Materia.objects.get(id=request.POST['materia'])
            mai = materia.id
            mat_exporta=MateriaExterna.objects.get(materia=materia)
            result = {"err":0,"ni":materia.nivel.id}
            if materia.materiaexterna_set.exists():
                try:
                    result = materia.materia_externa().exportar_datos()
                    exportada = materia.materia_externa()
                    if result['err']==0:
                        exportada.exportada = True
                        exportada.save()
                        mat_exporta.cantexport = mat_exporta.cantexport + 1
                        mat_exporta.exportada=True
                        result['mensaje2']  = ' SE HA EXPORTADO:' + str(mat_exporta.cantexport) + 'VECES'
                        mat_exporta.save()
                        if  EMAIL_ACTIVE and mat_exporta.cantexport > 1:
                            mat_exporta.enviar_correo()
                        if result['tot_wrn'] > 0 :
                            mat_exporta.correo_noexporta(result['tot_wrn'],result['datos'])
                    else:
                        if not mat_exporta.exportada:
                            exportada.exportada = False
                            exportada.save()
                except:
                    result = {"err":1,"ni":materia.nivel.id}
            result["ni"] = materia.nivel.id
            return HttpResponse(json.dumps(result),content_type="application/json")
    else:
        data = {'title': 'Importacion de materias de fuentes externas'}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
        else:
            fuentes = EntidadImportacion.objects.filter(activa=True)
            data['fuentesexternas'] = fuentes

    return render(request ,"materias_externas/fuentes.html" ,  data)
