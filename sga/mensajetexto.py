from datetime import datetime
import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from suds.client import Client
import unicodedata
import xlwt
from decorators import secure_module
from settings import MEDIA_ROOT, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID, SISTEMAS_GROUP_ID
from sga.commonviews import addUserData
from sga.models import FILTROS_MENSAJE, Profesor, TituloInstitucion, MensajesEnviado, Egresado, Graduado, RetiradoMatricula, Persona, Matricula, EstudiantesXDesertar, PreInscripcion, Absentismo, Inscripcion, Carrera

__author__ = 'jurgiles'


def elimina_tildes(cadena):
    s = ''.join((c for c in unicodedata.normalize('NFD',str(cadena)) if unicodedata.category(c) != 'Mn'))
    return s

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action'].lower()
            if action == 'docentes':
                contador = 0
                registros = 0
                try:
                    data = {}
                    data['result'] = 'ok'
                    listapersona = []
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    c = 0
                    registros = len(Profesor.objects.filter(activo=True))
                    data['registros'] = registros
                    for d in Profesor.objects.filter(activo=True):
                        i = 0
                        comprobar = ''
                        while ( i < 10):
                            try:
                                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', d.persona.telefono, request.POST['mensaje'])
                                # comprobar =  '3'
                                i = 10
                            except Exception as e:
                                i = i + 1
                            if comprobar == '4':
                                return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                        if comprobar != '0':
                            c = c + 1
                            listapersona.append([c,elimina_tildes(d.persona.nombre_completo()),d.persona.telefono])
                        elif comprobar == '0':
                            contador = contador + 1
                            mensajeenviado = MensajesEnviado(nombre = elimina_tildes(d.persona.nombre_completo()),
                                                            celular = d.persona.telefono,
                                                            filtro = request.POST['action'],
                                                            mensaje = request.POST['mensaje'],
                                                            fecha = datetime.now(),
                                                            user = request.user)
                            mensajeenviado.save()

                    data['contador'] = contador
                    data['listapersona'] = [{"id": str(x[0]),"nombre":elimina_tildes(x[1]),"celular":x[2]} for x in listapersona]
                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','contador':contador,'registros':registros}),content_type="application/json")
            elif action == 'egresados':
                contador = 0
                registros = 0
                try:
                    data = {}
                    data['result'] = 'ok'
                    listapersona = []
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    c = 0
                    g=Graduado.objects.all().values('inscripcion')
                    carrera = Carrera.objects.filter(id=request.POST['id'])[:1].get()
                    registros = len(Egresado.objects.filter(inscripcion__carrera=carrera).exclude(inscripcion__in=g))
                    data['registros'] = registros
                    for d in Egresado.objects.filter(inscripcion__carrera=carrera).exclude(inscripcion__in=g):
                        i = 0
                        comprobar = ''
                        while ( i < 10):
                            try:
                                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', d.inscripcion.persona.telefono, request.POST['mensaje'])
                                # comprobar =  '3'
                                i = 10
                            except Exception as e:
                                i = i + 1
                            if comprobar == '4':
                                return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                        if comprobar != '0':
                            c = c + 1
                            listapersona.append([c,elimina_tildes(d.inscripcion.persona.nombre_completo()),d.inscripcion.persona.telefono])
                        elif comprobar == '0':
                            contador = contador + 1
                            mensajeenviado = MensajesEnviado(nombre = elimina_tildes(d.inscripcion.persona.nombre_completo()),
                                                            celular = d.inscripcion.persona.telefono,
                                                            filtro = request.POST['action'],
                                                            mensaje = request.POST['mensaje'],
                                                            carrera_id = request.POST['id'],
                                                            fecha = datetime.now(),
                                                            user = request.user)
                            mensajeenviado.save()

                    data['contador'] = contador
                    if Egresado.objects.filter(inscripcion__carrera=carrera).exists():
                        data['listapersona'] = [{"id": str(x[0]),"nombre":elimina_tildes(x[1]),"celular":x[2]} for x in listapersona]
                        return HttpResponse(json.dumps(data),content_type="application/json")
                    return HttpResponse(json.dumps({'result':'noinfo'}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','contador':contador,'registros':registros}),content_type="application/json")
            elif action == 'graduados':
                contador = 0
                registros = 0
                try:
                    data = {}
                    data['result'] = 'ok'
                    listapersona = []
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    c = 0
                    carrera = Carrera.objects.filter(id=request.POST['id'])[:1].get()
                    registros = len(Graduado.objects.filter(inscripcion__carrera=carrera))
                    data['registros'] = registros
                    for d in Graduado.objects.filter(inscripcion__carrera=carrera):
                        i = 0
                        comprobar = ''
                        while ( i < 10):
                            try:
                                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', d.inscripcion.persona.telefono, request.POST['mensaje'])
                                # comprobar =  '3'
                                i = 10
                            except Exception as e:
                                i = i + 1
                            if comprobar == '4':
                                return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                        if comprobar != '0':
                            c = c + 1
                            listapersona.append([c,elimina_tildes(d.inscripcion.persona.nombre_completo()),d.inscripcion.persona.telefono])
                        elif comprobar == '0':
                            contador = contador + 1
                            mensajeenviado = MensajesEnviado(nombre = elimina_tildes(d.inscripcion.persona.nombre_completo()),
                                                            celular = d.inscripcion.persona.telefono,
                                                            filtro = request.POST['action'],
                                                            mensaje = request.POST['mensaje'],
                                                            carrera_id = request.POST['id'],
                                                            fecha = datetime.now(),
                                                            user = request.user)
                            mensajeenviado.save()

                    data['contador'] = contador
                    if Graduado.objects.filter(inscripcion__carrera=carrera).exists():
                        data['listapersona'] = [{"id": str(x[0]),"nombre":elimina_tildes(x[1]),"celular":x[2]} for x in listapersona]
                        return HttpResponse(json.dumps(data),content_type="application/json")
                    return HttpResponse(json.dumps({'result':'noinfo'}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','contador':contador,'registros':registros}),content_type="application/json")
            elif action == 'retirados':
                contador = 0
                registros = 0
                try:
                    data = {}
                    data['result'] = 'ok'
                    listapersona = []
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    c = 0
                    carrera = Carrera.objects.filter(id=request.POST['id'])[:1].get()
                    registros = len(RetiradoMatricula.objects.filter(inscripcion__carrera=carrera,activo=True))
                    data['registros'] = registros
                    for d in RetiradoMatricula.objects.filter(activo=True,inscripcion__carrera=carrera):
                        i = 0
                        comprobar = ''
                        while ( i < 10):
                            try:
                                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', d.inscripcion.persona.telefono, request.POST['mensaje'])
                                # comprobar =  '3'
                                i = 10
                            except Exception as e:
                                i = i + 1
                            if comprobar == '4':
                                return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                        if comprobar != '0':
                            c = c + 1
                            listapersona.append([c,elimina_tildes(d.inscripcion.persona.nombre_completo()),d.inscripcion.persona.telefono])
                        elif comprobar == '0':
                            contador = contador + 1
                            mensajeenviado = MensajesEnviado(nombre = elimina_tildes(d.inscripcion.persona.nombre_completo()),
                                                            celular = d.inscripcion.persona.telefono,
                                                            filtro = request.POST['action'],
                                                            mensaje = request.POST['mensaje'],
                                                            carrera_id = request.POST['id'],
                                                            fecha = datetime.now(),
                                                            user = request.user)
                            mensajeenviado.save()

                    data['contador'] = contador
                    if RetiradoMatricula.objects.filter(activo=True,inscripcion__carrera=carrera).exists():
                        data['listapersona'] = [{"id": str(x[0]),"nombre":elimina_tildes(x[1]),"celular":x[2]} for x in listapersona]
                        return HttpResponse(json.dumps(data),content_type="application/json")
                    return HttpResponse(json.dumps({'result':'noinfo'}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','contador':contador,'registros':registros}),content_type="application/json")
            elif action == 'administrativos':
                contador = 0
                registros = 0
                try:
                    data = {}
                    data['result'] = 'ok'
                    listapersona = []
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    c = 0
                    gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID,SISTEMAS_GROUP_ID]

                    registros = len(Persona.objects.filter(usuario__is_active=True).exclude(usuario__groups__id__in=gruposexcluidos))
                    data['registros'] = registros
                    for d in Persona.objects.filter(usuario__is_active=True).exclude(usuario__groups__id__in=gruposexcluidos):
                        i = 0
                        comprobar = ''
                        while ( i < 10):
                            try:
                                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', d.telefono, request.POST['mensaje'])
                                # comprobar =  '3'
                                i = 10
                            except Exception as e:
                                i = i + 1
                            if comprobar == '4':
                                return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                        if comprobar != '0':
                            c = c + 1
                            listapersona.append([c,elimina_tildes(d.nombre_completo()),d.telefono])
                        elif comprobar == '0':
                            contador = contador + 1
                            mensajeenviado = MensajesEnviado(nombre = elimina_tildes(d.nombre_completo()),
                                                            celular = d.telefono,
                                                            filtro = request.POST['action'],
                                                            mensaje = request.POST['mensaje'],
                                                            fecha = datetime.now(),
                                                            user = request.user)
                            mensajeenviado.save()

                    data['contador'] = contador
                    data['listapersona'] = [{"id": str(x[0]),"nombre":elimina_tildes(x[1]),"celular":x[2]} for x in listapersona]
                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','contador':contador,'registros':registros}),content_type="application/json")
            elif action == 'becados':
                contador = 0
                registros = 0
                try:
                    data = {}
                    data['result'] = 'ok'
                    listapersona = []
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    c = 0
                    registros = len(Matricula.objects.filter(becado=True, nivel__periodo__id=request.POST['id']))
                    data['registros'] = registros
                    for d in Matricula.objects.filter(becado=True, nivel__periodo__id=request.POST['id']):
                        i = 0
                        comprobar = ''
                        while ( i < 10):
                            try:
                                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', d.inscripcion.persona.telefono, request.POST['mensaje'])
                                # comprobar =  '3'
                                i = 10
                            except Exception as e:
                                i = i + 1
                            if comprobar == '4':
                                return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                        if comprobar != '0':
                            c = c + 1
                            listapersona.append([c,elimina_tildes(d.inscripcion.persona.nombre_completo()),d.inscripcion.persona.telefono])
                        elif comprobar == '0':
                            contador = contador + 1
                            mensajeenviado = MensajesEnviado(nombre = elimina_tildes(d.inscripcion.persona.nombre_completo()),
                                                            celular = d.inscripcion.persona.telefono,
                                                            filtro = request.POST['action'],
                                                            mensaje = request.POST['mensaje'],
                                                            periodo_id=request.POST['id'],
                                                            fecha = datetime.now(),
                                                            user = request.user)
                            mensajeenviado.save()

                    data['contador'] = contador
                    if Matricula.objects.filter(becado=True, nivel__periodo__id=request.POST['id']).exists():
                        data['listapersona'] = [{"id": str(x[0]),"nombre":elimina_tildes(x[1]),"celular":x[2]} for x in listapersona]
                        return HttpResponse(json.dumps(data),content_type="application/json")
                    return HttpResponse(json.dumps({'result':'noinfo'}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','contador':contador,'registros':registros}),content_type="application/json")
            elif action == 'desertores':
                contador = 0
                registros = 0
                try:
                    data = {}
                    data['result'] = 'ok'
                    listapersona = []
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    c = 0
                    registros = len(EstudiantesXDesertar.objects.filter(reintegro=False))
                    data['registros'] = registros
                    for d in EstudiantesXDesertar.objects.filter(reintegro=False):
                        i = 0
                        comprobar = ''
                        while ( i < 10):
                            try:
                                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', d.inscripcion.persona.telefono, request.POST['mensaje'])
                                # comprobar =  '3'
                                i = 10
                            except Exception as e:
                                i = i + 1
                            if comprobar == '4':
                                return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                        if comprobar != '0':
                            c = c + 1
                            listapersona.append([c,elimina_tildes(d.inscripcion.persona.nombre_completo()),d.inscripcion.persona.telefono])
                        elif comprobar == '0':
                            contador = contador + 1
                            mensajeenviado = MensajesEnviado(nombre = elimina_tildes(d.inscripcion.persona.nombre_completo()),
                                                            celular = d.inscripcion.persona.telefono,
                                                            filtro = request.POST['action'],
                                                            mensaje = request.POST['mensaje'],
                                                            fecha = datetime.now(),
                                                            user = request.user)
                            mensajeenviado.save()

                    data['contador'] = contador
                    if EstudiantesXDesertar.objects.filter(reintegro=False).exists():
                        data['listapersona'] = [{"id": str(x[0]),"nombre":elimina_tildes(x[1]),"celular":x[2]} for x in listapersona]
                        return HttpResponse(json.dumps(data),content_type="application/json")
                    return HttpResponse(json.dumps({'result':'noinfo'}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','contador':contador,'registros':registros}),content_type="application/json")
            elif action == 'preinscripcion':
                contador = 0
                registros = 0
                try:
                    data = {}
                    data['result'] = 'ok'
                    listapersona = []
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    c = 0
                    registros = len(PreInscripcion.objects.filter(inscrito=False))
                    data['registros'] = registros
                    for d in PreInscripcion.objects.filter(inscrito=False):
                        i = 0
                        comprobar = ''
                        while ( i < 10):
                            try:
                                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', d.celular, request.POST['mensaje'])
                                # comprobar =  '3'
                                i = 10
                            except Exception as e:
                                i = i + 1
                            if comprobar == '4':
                                return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                        nombres = elimina_tildes(d.nombres) +' '+elimina_tildes(d.apellido1)+' '+elimina_tildes(d.apellido2)
                        if comprobar != '0':
                            c = c + 1
                            listapersona.append([c,nombres,d.celular])
                        elif comprobar == '0':
                            contador = contador + 1
                            mensajeenviado = MensajesEnviado(nombre = nombres,
                                                            celular = d.celular,
                                                            filtro = request.POST['action'],
                                                            mensaje = request.POST['mensaje'],
                                                            fecha = datetime.now(),
                                                            user = request.user)
                            mensajeenviado.save()

                    data['contador'] = contador
                    if PreInscripcion.objects.filter(inscrito=False).exists():
                        data['listapersona'] = [{"id": str(x[0]),"nombre":elimina_tildes(x[1]),"celular":x[2]} for x in listapersona]
                        return HttpResponse(json.dumps(data),content_type="application/json")
                    return HttpResponse(json.dumps({'result':'noinfo'}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','contador':contador,'registros':registros}),content_type="application/json")

            elif action == 'absentismo':
                contador = 0
                registros = 0
                try:
                    data = {}
                    data['result'] = 'ok'
                    listapersona = []
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    c = 0
                    carrera = Carrera.objects.filter(id=request.POST['id'])[:1].get()
                    registros = len(Absentismo.objects.filter(reintegro=False,finalizado=False,materiaasignada__matricula__inscripcion__carrera=carrera))
                    data['registros'] = registros
                    for d in Absentismo.objects.filter(reintegro=False,finalizado=False,materiaasignada__matricula__inscripcion__carrera=carrera):
                        i = 0
                        comprobar = ''
                        while ( i < 10):
                            try:
                                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', d.materiaasignada.matricula.inscripcion.persona.telefono, request.POST['mensaje'])
                                # comprobar =  '3'
                                i = 10
                            except Exception as e:
                                i = i + 1
                            if comprobar == '4':
                                return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                        if comprobar != '0':
                            c = c + 1
                            listapersona.append([c,elimina_tildes(d.materiaasignada.matricula.inscripcion.persona.nombre_completo()),d.materiaasignada.matricula.inscripcion.persona.telefono])
                        elif comprobar == '0':
                            contador = contador + 1
                            mensajeenviado = MensajesEnviado(nombre = elimina_tildes(d.materiaasignada.matricula.inscripcion.persona.nombre_completo()),
                                                            celular = d.materiaasignada.matricula.inscripcion.persona.telefono,
                                                            filtro = request.POST['action'],
                                                            mensaje = request.POST['mensaje'],
                                                            carrera_id = request.POST['id'],
                                                            fecha = datetime.now(),
                                                            user = request.user)
                            mensajeenviado.save()

                    data['contador'] = contador
                    if Absentismo.objects.filter(reintegro=False,finalizado=False).exists():
                        data['listapersona'] = [{"id": str(x[0]),"nombre":elimina_tildes(x[1]),"celular":x[2]} for x in listapersona]
                        return HttpResponse(json.dumps(data),content_type="application/json")
                    return HttpResponse(json.dumps({'result':'noinfo'}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','contador':contador,'registros':registros}),content_type="application/json")
            elif action == 'grupo':
                contador = 0
                registros = 0
                try:
                    data = {}
                    data['result'] = 'ok'
                    listapersona = []
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    c = 0
                    registros = len(Matricula.objects.filter(nivel__grupo__id=request.POST['id'],inscripcion__user__is_active=True))
                    data['registros'] = registros
                    for d in Matricula.objects.filter(nivel__grupo__id=request.POST['id'],inscripcion__user__is_active=True):
                        i = 0
                        comprobar = ''
                        while ( i < 10):
                            try:
                                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', d.inscripcion.persona.telefono, request.POST['mensaje'])
                                # comprobar =  '3'
                                i = 10
                            except Exception as e:
                                i = i + 1
                            if comprobar == '4':
                                return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                        if comprobar != '0':
                            c = c + 1
                            listapersona.append([c,elimina_tildes(d.inscripcion.persona.nombre_completo()),d.inscripcion.persona.telefono])
                        elif comprobar == '0':
                            contador = contador + 1
                            mensajeenviado = MensajesEnviado(nombre = elimina_tildes(d.inscripcion.persona.nombre_completo()),
                                                            celular = d.inscripcion.persona.telefono,
                                                            filtro = request.POST['action'],
                                                            mensaje = request.POST['mensaje'],
                                                            grupo_id=request.POST['id'],
                                                            fecha = datetime.now(),
                                                            user = request.user)
                            mensajeenviado.save()

                    data['contador'] = contador
                    if Matricula.objects.filter(nivel__grupo__id=request.POST['id'],inscripcion__user__is_active=True).exists():
                        data['listapersona'] = [{"id": str(x[0]),"nombre":elimina_tildes(x[1]),"celular":x[2]} for x in listapersona]
                        return HttpResponse(json.dumps(data),content_type="application/json")
                    return HttpResponse(json.dumps({'result':'noinfo'}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','contador':contador,'registros':registros}),content_type="application/json")
            elif action == 'nivel':
                contador = 0
                registros = 0
                try:
                    data = {}
                    data['result'] = 'ok'
                    listapersona = []
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    c = 0
                    registros = len(Matricula.objects.filter(nivel__id=request.POST['id'],inscripcion__user__is_active=True))
                    data['registros'] = registros
                    for d in Matricula.objects.filter(nivel__id=request.POST['id'],inscripcion__user__is_active=True):
                        i = 0
                        comprobar = ''
                        while ( i < 10):
                            try:
                                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', d.inscripcion.persona.telefono, request.POST['mensaje'])
                                # comprobar =  '3'
                                i = 10
                            except Exception as e:
                                i = i + 1
                            if comprobar == '4':
                                return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                        if comprobar != '0':
                            c = c + 1
                            listapersona.append([c,elimina_tildes(d.inscripcion.persona.nombre_completo()),d.inscripcion.persona.telefono])
                        elif comprobar == '0':
                            contador = contador + 1
                            mensajeenviado = MensajesEnviado(nombre = elimina_tildes(d.inscripcion.persona.nombre_completo()),
                                                            celular = d.inscripcion.persona.telefono,
                                                            filtro = request.POST['action'],
                                                            mensaje = request.POST['mensaje'],
                                                            nivel_id=request.POST['id'],
                                                            fecha = datetime.now(),
                                                            user = request.user)
                            mensajeenviado.save()

                    data['contador'] = contador
                    if Matricula.objects.filter(nivel__id=request.POST['id'],inscripcion__user__is_active=True).exists():
                        data['listapersona'] = [{"id": str(x[0]),"nombre":elimina_tildes(x[1]),"celular":x[2]} for x in listapersona]
                        return HttpResponse(json.dumps(data),content_type="application/json")
                    return HttpResponse(json.dumps({'result':'noinfo'}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','contador':contador,'registros':registros}),content_type="application/json")
            elif action == 'periodo':
                contador = 0
                registros = 0
                try:
                    data = {}
                    data['result'] = 'ok'
                    listapersona = []
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    c = 0
                    registros = len(Matricula.objects.filter(nivel__periodo__id=request.POST['id'],inscripcion__user__is_active=True))
                    data['registros'] = registros
                    for d in Matricula.objects.filter(nivel__periodo__id=request.POST['id'],inscripcion__user__is_active=True):
                        i = 0
                        comprobar = ''
                        while ( i < 10):
                            try:
                                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', d.inscripcion.persona.telefono, request.POST['mensaje'])
                                # comprobar =  '3'
                                i = 10
                            except Exception as e:
                                i = i + 1
                            if comprobar == '4':
                                return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                        if comprobar != '0':
                            c = c + 1
                            listapersona.append([c,elimina_tildes(d.inscripcion.persona.nombre_completo()),d.inscripcion.persona.telefono])
                        elif comprobar == '0':
                            contador = contador + 1
                            mensajeenviado = MensajesEnviado(nombre = elimina_tildes(d.inscripcion.persona.nombre_completo()),
                                                            celular = d.inscripcion.persona.telefono,
                                                            filtro = request.POST['action'],
                                                            mensaje = request.POST['mensaje'],
                                                            periodo_id=request.POST['id'],
                                                            fecha = datetime.now(),
                                                            user = request.user)
                            mensajeenviado.save()

                    data['contador'] = contador
                    if Matricula.objects.filter(nivel__periodo__id=request.POST['id'],inscripcion__user__is_active=True).exists():
                        data['listapersona'] = [{"id": str(x[0]),"nombre":elimina_tildes(x[1]),"celular":x[2]} for x in listapersona]
                        return HttpResponse(json.dumps(data),content_type="application/json")
                    return HttpResponse(json.dumps({'result':'noinfo'}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','contador':contador,'registros':registros}),content_type="application/json")
            elif action == 'carrera':
                contador = 0
                registros = 0
                try:
                    data = {}
                    data['result'] = 'ok'
                    listapersona = []
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    c = 0
                    carrera = Carrera.objects.filter(id=request.POST['id'])[:1].get()
                    registros = len(Matricula.objects.filter(inscripcion__carrera=carrera))
                    data['registros'] = registros
                    for d in Matricula.objects.filter(inscripcion__carrera=carrera):
                        i = 0
                        comprobar = ''
                        while ( i < 10):
                            try:
                                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', d.inscripcion.persona.telefono, request.POST['mensaje'])
                                # comprobar =  '3'
                                i = 10
                            except Exception as e:
                                i = i + 1
                            if comprobar == '4':
                                return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                        if comprobar != '0':
                            c = c + 1
                            listapersona.append([c,elimina_tildes(d.inscripcion.persona.nombre_completo()),d.inscripcion.persona.telefono])
                        elif comprobar == '0':
                            contador = contador + 1
                            mensajeenviado = MensajesEnviado(nombre = elimina_tildes(d.inscripcion.persona.nombre_completo()),
                                                            celular = d.inscripcion.persona.telefono,
                                                            filtro = request.POST['action'],
                                                            mensaje = request.POST['mensaje'],
                                                            carrera_id=request.POST['id'],
                                                            fecha = datetime.now(),
                                                            user = request.user)
                            mensajeenviado.save()

                    data['contador'] = contador
                    if Matricula.objects.filter(inscripcion__carrera=carrera).exists():
                        data['listapersona'] = [{"id": str(x[0]),"nombre":elimina_tildes(x[1]),"celular":x[2]} for x in listapersona]
                        return HttpResponse(json.dumps(data),content_type="application/json")
                    return HttpResponse(json.dumps({'result':'noinfo'}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','contador':contador,'registros':registros}),content_type="application/json")
            elif action == 'manual':
                try:
                    data = {}
                    data['result'] = 'ok'
                    client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
                    numeros = request.POST['id'].split(',')
                    listapersona = []
                    c = 0
                    i=0
                    comprobar = ''
                    for t in range(len(numeros)):
                        while ( i < 10):
                            try:
                                comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', numeros[t], request.POST['mensaje'])
                                i = 10
                            except Exception as e:
                                i = i + 1
                            if comprobar == '4':
                                return HttpResponse(json.dumps({'result':'badmensj'}),content_type="application/json")
                            c = c + 1
                            listapersona.append([c,comprobar,numeros[t]])
                    data['listapersona'] = [{"id": str(x[0]),"nombre":elimina_tildes(x[1]),"celular":x[2]} for x in listapersona]
                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
            elif action == 'crearexcel':
                try:
                    datos = json.loads(request.POST['datos'])
                    #egresados = Egresado.objects.filter(inscripcion__carrera=carrera).order_by('inscripcion__persona__apellido1','inscripcion__persona__apellido2')
                    m = 2
                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0,0,m+2, tit.nombre , titulo2)
                    ws.write_merge(1, 1,0,m+2, 'PERSONAS QUE NO SE ENVIO EL MENSAJE ', titulo2)

                    fila = 2
                    detalle = 3
                    c=0
                    for e in datos:
                        c=c+1
                        fila = fila +1
                        columna=0
                        ws.write_merge(fila,fila,columna,2 , e['nombre'])
                        ws.write_merge(fila,fila,columna+3,4 , e['celular'])

                    detalle = detalle + fila
                    ws.write(detalle, 0, "Fecha Impresion", subtitulo)
                    ws.write(detalle, 2, str(datetime.now()), subtitulo)
                    detalle=detalle +1
                    ws.write(detalle, 0, "Usuario", subtitulo)
                    ws.write(detalle, 2, str(request.user), subtitulo)

                    nombre =request.POST['accionfiltro']+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":str(ex)}),content_type="application/json")

        else:
            data = {'titulo':'Envio de mesaje'}
            addUserData(request,data)
            client = Client('http://online.publimes.com:5000/Service.svc?wsdl')
            # numeros = ['0986656832']
            #
            # for i in range(len(numeros)):
            #     comprobar =  client.service.EnviarMensaje( 79,'TECBO14593', 'C', numeros[i], 'saaa')
            data['FILTROS_MENSAJE'] = FILTROS_MENSAJE
            return render(request ,"mensajetexto/mensajetexto.html" ,  data)
    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))
