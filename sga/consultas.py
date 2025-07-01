from datetime import datetime, time, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator
import json
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from settings import DEFAULT_PASSWORD, PROFESORES_GROUP_ID, PAGO_ESTRICTO, DATOS_ESTRICTO
from sga.commonviews import addUserData
from sga.forms import ProfesorForm
from sga.models import Profesor, Persona, LeccionGrupo, EvaluacionLeccion, AsistenciaLeccion, Turno, Aula, Sede, Clase, Leccion, Sesion, EvaluacionIAVQ, Periodo


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
        data = {'title': 'Listado de Docentes'}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'horario':
                try:
                    profesor = Profesor.objects.get(pk=request.GET['id'])
                    data['disponible'] = LeccionGrupo.objects.filter(profesor=profesor,abierta=True).count()==0
                    if not data['disponible']:
                        data['lecciongrupo'] = LeccionGrupo.objects.filter(profesor=profesor,abierta=True)[0]
                    data['title'] = 'Horario del Profesor'
                    data['profesor'] = profesor
                    data['semana'] = ['Lunes','Martes','Miercoles','Jueves','Viernes', 'Sabado', 'Domingo']
                    data['sesiones'] = Sesion.objects.all()

                    hoy = datetime.now().date()
                    clases = Clase.objects.filter(materia__nivel__periodo__activo=True,materia__inicio__lte=hoy, materia__fin__gte=hoy, materia__profesormateria__profesor=profesor, materia__profesormateria__desde__lte=hoy, materia__profesormateria__hasta__gte=hoy).order_by('materia__inicio')
                    clasespm = [(x, x.materia.profesormateria_set.filter(profesor=profesor)[:1].get()) for x in clases]
                    data['clases'] = clasespm

                    data['periodo'] = request.session['periodo']
                    return render(request ,"consultas/horariosbs.html" ,  data)
                except :
                    return HttpResponseRedirect("/")

            elif action == 'asistencia':
                try:
                    profesor = Profesor.objects.get(pk=request.GET['id'])
#                    data['disponible'] = LeccionGrupo.objects.filter(profesor=profesor,abierta=True).count()==0
#                    if not data['disponible']:
#                        data['lecciongrupo'] = LeccionGrupo.objects.get(profesor=profesor,abierta=True)
                    data['title'] = 'Asistencia del Profesor'
                    data['profesor'] = profesor
                    data['semana'] = ['Lunes','Martes','Miercoles','Jueves','Viernes']
                    data['sesiones'] = Sesion.objects.all()
                    data['clases'] = Clase.objects.filter(profesor=profesor)
                    data['semanas'] = Periodo.periodo_vigente().semanas()
                    return render(request ,"consultas/asistenciasbs.html" ,  data)
                except:
                    return HttpResponseRedirect("/")
            elif action=='asistenciaclase':
                materiaid = request.GET['materiaid']
                profesorid = request.GET['profesorid']
                turnoid = request.GET['turnoid']
                aulaid = request.GET['aulaid']
                dia = int(request.GET['dia'])

                semana1 = int(request.GET['desde'])
                semana2 = int(request.GET['hasta'])
                semanas = Periodo.periodo_vigente().semanas()
                data = {}
                data['leccionesgrupo'] = LeccionGrupo.objects.filter(materia=materiaid, profesor=profesorid,\
                    turno=turnoid, aula=aulaid, dia=dia,\
                    fecha__gte=semanas[semana1][0], fecha__lte=semanas[semana2][1])
                cantidad = data['leccionesgrupo'].count()
                finicio = semanas[semana1][0] + timedelta(dia-1)
                fechas = []
                while (finicio <= semanas[semana2][1]):
                    lg_id = data['leccionesgrupo'].get(fecha=finicio).id if data['leccionesgrupo'].filter(fecha=finicio).count()>0 else None
                    tmp = (finicio, data['leccionesgrupo'].filter(fecha=finicio).count()>0, lg_id )
                    fechas.append(tmp)
                    finicio = finicio + timedelta(7)
                data['fechas'] = fechas
                data['plan'] = len(fechas)
                if cantidad>data['plan']:
                    cantidad = data['plan']
                data['real'] = cantidad
                data['pct'] = (cantidad/float(data['plan']))*100.0
                data['horas'] = Turno.objects.get(pk=turnoid).duracion() * cantidad
                return render(request ,"consultas/tablaclases.html" ,  data)

            elif action=='asistenciaclaseresumen':
                profesorid = request.GET['profesorid']
                dia = int(request.GET['dia'])

                semana1 = int(request.GET['desde'])
                semana2 = int(request.GET['hasta'])
                semanas = Periodo.periodo_vigente().semanas()


                data = {}
                data['leccionesgrupo'] = LeccionGrupo.objects.filter(profesor=profesorid,\
                    dia=dia,\
                    fecha__gte=semanas[semana1][0], fecha__lte=semanas[semana2][1])
                cantidad = data['leccionesgrupo'].count()
#                if cantidad>data['plan']:
#                    cantidad = data['plan']
                data['real'] = cantidad
#                data['pct'] = (cantidad/float(data['plan']))*100.0
                if cantidad>0:
                    horas = reduce(lambda a, b: a+b, [timedelta(hours=x.turno.termina.hour,minutes=x.turno.termina.minute) - timedelta(hours=x.turno.comienza.hour, minutes=x.turno.comienza.minute) for x in data['leccionesgrupo']])
                    data['horas'] = horas.days * 24 + horas.seconds/60/60
                else:
                    data['horas'] = 0
#                return HttpResponse( str(data['real'])+"clases " + str(data['horas'])+" Horas")
                return render(request ,"consultas/tablaresumen.html" ,  data)
            elif action=='asistenciaclasetotal':
                profesorid = request.GET['profesorid']

                semana1 = int(request.GET['desde'])
                semana2 = int(request.GET['hasta'])
                semanas = Periodo.periodo_vigente().semanas()

                data = {}
                data['leccionesgrupo'] = LeccionGrupo.objects.filter(profesor=profesorid,\
                    fecha__gte=semanas[semana1][0], fecha__lte=semanas[semana2][1])
                cantidad = data['leccionesgrupo'].count()
                #                if cantidad>data['plan']:
                #                    cantidad = data['plan']
                data['real'] = cantidad
                #                data['pct'] = (cantidad/float(data['plan']))*100.0
                if cantidad>0:
                    horas = reduce(lambda a, b: a+b, [timedelta(hours=x.turno.termina.hour,minutes=x.turno.termina.minute) - timedelta(hours=x.turno.comienza.hour, minutes=x.turno.comienza.minute) for x in data['leccionesgrupo']])
                    data['horas'] = horas.days*24 + horas.seconds/60/60
                else:
                    data['horas'] = 0
                #                return HttpResponse( str(data['real'])+"clases " + str(data['horas'])+" Horas")
                return render(request ,"consultas/tablatotal.html" ,  data)


        else:
            search = None
            if 's' in request.GET:
                search = request.GET['s']
            if search:
                profesores = Profesor.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search)).order_by('persona__apellido1')
            else:
                profesores = Profesor.objects.filter(activo=True).order_by('persona__apellido1')

            paging = Paginator(profesores, 50)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)
            data['paging'] = paging
            data['page'] = page
            # data['periodo'] = Periodo.periodo_vigente()
            data['search'] = search if search else ""
            data['profesores'] = page.object_list
            return render(request ,"consultas/ver_horariobs.html" ,  data)