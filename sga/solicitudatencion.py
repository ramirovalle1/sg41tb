import json

from django.db import transaction
from django.db.models import  Max
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from datetime import datetime
from sga.models import TipoIdentificacion, TipoServicioCarrera, SolicitudAntencion, viewTodaPersona, Pais, Provincia, Canton


def view(request):
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'agregarsolicitud':
            try:
                data = {'title': ''}

                sid = transaction.savepoint()

                fecha= datetime.now().strftime("%Y-%m-%d")
                hora_actual = datetime.now().time()

                tipoidentificacion = TipoIdentificacion.objects.get(pk=int(request.POST['tipoidenticacion']))
                tiposervicio = TipoServicioCarrera.objects.get(pk=int(request.POST['tiposervicio']))


                solicitud = SolicitudAntencion(tipoidentificacion=tipoidentificacion,identificacion=str(request.POST['identificacion']).upper(),
                                               nombres=str(request.POST['nombres']).upper(),apellidos=str(request.POST['apellidos']).upper(),
                                               email=str(request.POST['email']).lower(),celular=str(request.POST['celular']),tiposervicio=tiposervicio,
                                               motivo=str(request.POST['requerimiento']).upper(),fecha=fecha,hora=hora_actual,
                                               pais_id=int(request.POST['idpais']),
                                               provincia_id=int(request.POST['idprovincia']),
                                               ciudad_id=int(request.POST['idciudad'])
                                 )

                solicitud.save()

                serie = 0
                valor = SolicitudAntencion.objects.filter(fecha=datetime.now().date()).aggregate(
                    Max('serie'))
                if valor['serie__max'] != None:
                    serie = valor['serie__max'] + 1

                solicitud.serie=serie
                solicitud.save()

                # solicitud.mail_asignaciondocente()

                transaction.savepoint_commit(sid)
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")

        if action == 'validaridentificacion':
            try:
                data = {'title': ''}

                if not viewTodaPersona.objects.filter(cedula=str(request.POST['cedu']).strip()).exists():
                    return HttpResponse(json.dumps({'result': 'bad',
                                                    'message': 'La Cedula o Passporte no se encuentra registrado '}),
                                       content_type="application/json")

                datospersona = viewTodaPersona.objects.filter(cedula=str(request.POST['cedu']).strip())[0]
                apellidos = ""
                if datospersona.apellido1:
                    apellidos = datospersona.apellido1
                if datospersona.apellido2:
                    apellidos = apellidos + datospersona.apellido2

                if datospersona.sexo_id == 1:
                    sexo = "Femenino"
                else:
                    sexo = "Masculino"

                data['datospersona'] = [{"cedula": datospersona.cedula,
                                         "apellidos": apellidos,
                                         "nombres": datospersona.nombres,
                                         "sexo": sexo,
                                         "email":datospersona.emailinst if datospersona.emailinst else 'SIN CORREO',
                                         "direccion": datospersona.direccion if datospersona.direccion else 'N/D',
                                         "ceular":datospersona.telefono if datospersona.telefono else "000000000"
                                         }]

                data['result'] = 'ok'

                return HttpResponse(json.dumps(data),content_type="application/json")

            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")


        if action == 'buscarcantones':
            try:
                data = {'title': ''}
                listCan= []
                listCan.append({"id": 0, "nombre": "Seleccionar el Canton"})
                if Canton.objects.filter(provincia__id=int(request.POST['idprovincia'])).order_by("nombre").exists():
                    for g in Canton.objects.filter(provincia__id=int(request.POST['idprovincia'])).order_by("nombre"):
                        listCan.append({"id": g.id, "nombre": g.nombre})
                data['listacanton'] = listCan
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")



    else:
        data = {'title': 'Solicitudes de Atencion'}

        data['listtipoidentificacion'] = TipoIdentificacion.objects.filter(estado=True).order_by("id")
        data['listtiposervicio'] = TipoServicioCarrera.objects.filter()
        data['listpais'] = Pais.objects.filter(pk=1)
        data['lisprovincia'] = Provincia.objects.filter()

        return render(request ,"teleatencion/solicitudatencion.html" ,  data)

