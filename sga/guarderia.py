from datetime import datetime,timedelta,time
from decimal import Decimal
import json
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from psycopg2._psycopg import Date
from decorators import secure_module
from datetime import datetime, date, timedelta
from sga.commonviews import addUserData, ip_client_address
from sga.forms import InscripcionGuarderiaForm, DetalleInscripcionGuarderiaForm, RegistroGuarderiaForm
from sga.models import InscripcionGuarderia, DetalleInscGuarderia, Inscripcion, Matricula, IngresoGuarderia


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            try:
                f = InscripcionGuarderiaForm(request.POST)
                if f.is_valid():
                    if request.POST['ban'] == 1:
                        mensaje = 'Adicionado'
                    else:
                        mensaje = 'Editado'
                    try:
                        if f.cleaned_data['tipopersona'].id == 2:
                            if  not InscripcionGuarderia.objects.filter(inscripcion__id=f.cleaned_data['inscripcion_id']).exists():

                                    ingreso = InscripcionGuarderia(inscripcion_id=f.cleaned_data['inscripcion_id'],
                                                                   tipopersona=f.cleaned_data['tipopersona'],
                                                                    fecha=datetime.now(),
                                                                    responsable=f.cleaned_data['responsable'],
                                                                    telresponsable=f.cleaned_data['telresponsable'],
                                                                    dirresponsable=f.cleaned_data['dirresponsable'],
                                                                    numhijos=f.cleaned_data['numhijos'],
                                                                    identificacion = f.cleaned_data['identificacion'],
                                                                    edadresponsable = f.cleaned_data['edadresponsable'],
                                                                    email=f.cleaned_data['email'])
                                    ingreso.save()
                                    return HttpResponseRedirect("/guarderia?action=idetalle&id="+str(ingreso.id))
                            else:
                                ingreso =InscripcionGuarderia.objects.filter(inscripcion__id=f.cleaned_data['inscripcion_id'])[:1].get()
                                ingreso.fecha=datetime.now()
                                ingreso.responsable=f.cleaned_data['responsable']
                                ingreso.telresponsable=f.cleaned_data['telresponsable']
                                ingreso.dirresponsable=f.cleaned_data['dirresponsable']
                                ingreso.numhijos=f.cleaned_data['numhijos']
                                ingreso.edadresponsable = f.cleaned_data['edadresponsable']
                                ingreso.email = f.cleaned_data['email']
                                ingreso.save()
                        else:
                            if f.cleaned_data['tipopersona'].id == 5 or f.cleaned_data['tipopersona'].id == 6:
                                if  not InscripcionGuarderia.objects.filter(id=f.cleaned_data['persona_id']).exists():

                                        ingreso = InscripcionGuarderia(personaext=f.cleaned_data['personaext'],
                                                                       tipopersona=f.cleaned_data['tipopersona'],
                                                                        fecha=datetime.now(),
                                                                        responsable=f.cleaned_data['responsable'],
                                                                        telresponsable=f.cleaned_data['telresponsable'],
                                                                        dirresponsable=f.cleaned_data['dirresponsable'],
                                                                        numhijos=f.cleaned_data['numhijos'],
                                                                        identificacion = f.cleaned_data['identificacion'],
                                                                        edadresponsable = f.cleaned_data['edadresponsable'],
                                                                        email=f.cleaned_data['email'])
                                        ingreso.save()
                                        return HttpResponseRedirect("/guarderia?action=idetalle&id="+str(ingreso.id))
                                else:
                                    ingreso =InscripcionGuarderia.objects.filter(id=f.cleaned_data['persona_id'])[:1].get()
                                    ingreso.fecha=datetime.now()
                                    ingreso.responsable=f.cleaned_data['responsable']
                                    ingreso.telresponsable=f.cleaned_data['telresponsable']
                                    ingreso.dirresponsable=f.cleaned_data['dirresponsable']
                                    ingreso.numhijos=f.cleaned_data['numhijos']
                                    ingreso.edadresponsable = f.cleaned_data['edadresponsable']
                                    ingreso.email = f.cleaned_data['email']
                                    ingreso.save()
                            else:
                                if  not InscripcionGuarderia.objects.filter(persona__id=f.cleaned_data['persona_id']).exists():

                                        ingreso = InscripcionGuarderia(persona_id=f.cleaned_data['persona_id'],
                                                                        fecha=datetime.now(),
                                                                        tipopersona=f.cleaned_data['tipopersona'],
                                                                        responsable=f.cleaned_data['responsable'],
                                                                        telresponsable=f.cleaned_data['telresponsable'],
                                                                        dirresponsable=f.cleaned_data['dirresponsable'],
                                                                        numhijos=f.cleaned_data['numhijos'],
                                                                        identificacion = f.cleaned_data['identificacion'],
                                                                        edadresponsable = f.cleaned_data['edadresponsable'],
                                                                        email=f.cleaned_data['email'])
                                        ingreso.save()
                                        return HttpResponseRedirect("/guarderia?action=idetalle&id="+str(ingreso.id))
                                else:
                                    ingreso =InscripcionGuarderia.objects.filter(persona__id=f.cleaned_data['persona_id'])[:1].get()
                                    ingreso.fecha=datetime.now()
                                    ingreso.responsable=f.cleaned_data['responsable']
                                    ingreso.telresponsable=f.cleaned_data['telresponsable']
                                    ingreso.dirresponsable=f.cleaned_data['dirresponsable']
                                    ingreso.numhijos=f.cleaned_data['numhijos']
                                    ingreso.edadresponsable = f.cleaned_data['edadresponsable']
                                    ingreso.email = f.cleaned_data['email']
                                    ingreso.save()


                        client_address = ip_client_address(request)

                    # Log Editar Inscripcion
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(ingreso).pk,
                            object_id       = ingreso.id,
                            object_repr     = force_str(ingreso),
                            action_flag     = CHANGE,
                            change_message  = mensaje + ' Inscripcion Guarderia (' + client_address + ')' )

                        return HttpResponseRedirect("/guarderia")



                    except  Exception as ex:
                        pass
            except Exception as ex:
                return HttpResponseRedirect("/guarderia")
        elif action == 'registrar':
            detalle = DetalleInscGuarderia.objects.get(pk=request.POST['id'])
            f = RegistroGuarderiaForm(request.POST)
            if f.is_valid():
                registro = IngresoGuarderia(detalle=detalle,
                                            horaentrada = f.cleaned_data['horaentrada'],
                                            horasalida = f.cleaned_data['horasalida'],
                                            fechaentrada = datetime.now(),
                                            observacion = f.cleaned_data['observacion'])
                registro.save()
                return HttpResponseRedirect("/guarderia?action=verdetalle&id="+str(detalle.inscripcionguarderia.id))

        elif action =='verfecha':
            try:
                a= int(request.POST['fecha'].split("-")[2])
                m=int(request.POST['fecha'].split("-")[1])
                d=int(request.POST['fecha'].split("-")[0])
                mm = datetime.now().date().month -1
                fecha = date(a,m,d)

                if int(request.POST['fecha'].split("-")[1]) > datetime.now().date().month:
                    anios =(datetime.now().date().year - (fecha).year)-1
                else:
                    if m == datetime.now().date().month and d > datetime.now().date().day :
                        anios =(datetime.now().date().year - (fecha).year) -1

                    else:
                        anios =(datetime.now().date().year - (fecha).year)
                if m >=  datetime.now().date().month:

                    if m > datetime.now().date().month:
                        meses =  fecha.month - datetime.now().date().month
                        meses =  11 - meses
                    else:
                        if d <= datetime.now().date().day :
                            meses = 0
                        else:
                            meses = 11

                else:
                    meses = (datetime.now().date().month -  fecha.month)-1

                if  m == datetime.now().date().month  and d <= datetime.now().date().day:
                    mm = datetime.now().date().month

                fechanueva =date( datetime.now().date().year,mm,int(request.POST['fecha'].split("-")[0]))

                dia =   (fechanueva - datetime.now().date()).days
                if dia < 0:
                    dia = dia * -1

                edad = str(anios) + ' anios ' + str(meses) + ' meses ' + str(dia)+' dias'

                return HttpResponse(json.dumps({"result":"ok","edad":str(edad)}),content_type="application/json")
            except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


        elif action == 'adddetalle':
            if 'salir' in request.POST :
                return HttpResponseRedirect("/guarderia")

            if 'ban' in request.POST:
                detalle = DetalleInscGuarderia.objects.get(pk=request.POST['id'])
                f = DetalleInscripcionGuarderiaForm(request.POST)
                if f.is_valid():
                    detalle.nombre=f.cleaned_data['nombre']
                    detalle.fechanacimiento=f.cleaned_data['fechanacimiento']
                    detalle.peso=f.cleaned_data['peso']
                    detalle.enfermedades=f.cleaned_data['enfermedades']
                    detalle.alergias=f.cleaned_data['alergias']
                    detalle.observacion=f.cleaned_data['observacion']
                    detalle.cedula = f.cleaned_data['cedula']
                    detalle.direccion = f.cleaned_data['direccion']
                    detalle.lugar = f.cleaned_data['lugar']

                    detalle.save()
                    if 'foto' in request.FILES:
                         detalle.foto= request.FILES['foto']
                         detalle.save()

                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(detalle).pk,
                        object_id       = detalle.id,
                        object_repr     = force_str(detalle),
                        action_flag     = CHANGE,
                        change_message  = 'Editado Detalle de  Inscripcion Guarderia (' + client_address + ')' )

                    if 'continuar' in request.POST:
                        return HttpResponseRedirect("/guarderia?action=idetalle&id="+str(detalle.inscripcionguarderia.id))
                    else:
                        return HttpResponseRedirect("/guarderia")

            else:
                ingreso =  InscripcionGuarderia.objects.get(pk=request.POST['id'])
                f = DetalleInscripcionGuarderiaForm(request.POST)
                if f.is_valid():
                    detalle = DetalleInscGuarderia(inscripcionguarderia=ingreso,
                                                   nombre=f.cleaned_data['nombre'],
                                                   fechanacimiento=f.cleaned_data['fechanacimiento'],
                                                   peso=f.cleaned_data['peso'],
                                                   enfermedades=f.cleaned_data['enfermedades'],
                                                   alergias=f.cleaned_data['alergias'],
                                                   observacion=f.cleaned_data['observacion'],
                                                   cedula = f.cleaned_data['cedula'],
                                                   direccion = f.cleaned_data['direccion'],
                                                   fecha_ins = datetime.now(),
                                                   lugar=f.cleaned_data['lugar'])
                    if 'foto' in request.FILES:
                         detalle.foto= request.FILES['foto']
                         detalle.save()
                    detalle.save()
                    client_address = ip_client_address(request)

                    # Log Editar Inscripcion
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(ingreso).pk,
                        object_id       = ingreso.id,
                        object_repr     = force_str(ingreso),
                        action_flag     = CHANGE,
                        change_message  = 'Adicionado Detalle de  Inscripcion Guarderia (' + client_address + ')' )


                    if 'continuar' in request.POST:
                        return HttpResponseRedirect("/guarderia?action=idetalle&id="+str(ingreso.id))
                    else:
                        return HttpResponseRedirect("/guarderia")


        return HttpResponseRedirect("/guarderia")
    else:
        data = {'title': 'Inscripcion Guarderia '}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'add':
                hoy = datetime.today().date()
                data['ban'] = 1
                data['form'] = InscripcionGuarderiaForm(initial = {'fecha':hoy} )

                return render(request ,"guarderia/add.html" ,  data)
            elif action =='idetalle':
                data['insc'] = InscripcionGuarderia.objects.get(pk=request.GET['id'])
                data['form'] = DetalleInscripcionGuarderiaForm()

                return render(request ,"guarderia/idetalle.html" ,  data)
            elif action == 'verdetalle':
                if 'info' in request.GET:
                    data['info'] =  request.GET['info']
                data['detalle'] = DetalleInscGuarderia.objects.filter(inscripcionguarderia__id=request.GET['id']).order_by('nombre')
                return render(request ,"guarderia/detalle.html" ,  data)

            elif action == 'editar':
                insc = InscripcionGuarderia.objects.get(pk=request.GET['id'])
                initial = model_to_dict(insc)
                data['form'] = InscripcionGuarderiaForm(initial =initial )
                data['ban'] = 2
                data['insc'] = insc
                return render(request ,"guarderia/add.html" ,  data)

            elif action == 'editard':
                insc = DetalleInscGuarderia.objects.get(pk=request.GET['id'])
                initial = model_to_dict(insc)
                data['form'] = DetalleInscripcionGuarderiaForm(initial =initial )
                data['ban'] = 2
                data['insc'] = insc
                return render(request ,"guarderia/idetalle.html" ,  data)

            elif action == 'registrar':
                periodo = request.session['periodo']
                insc = DetalleInscGuarderia.objects.get(pk=request.GET['id'])
                data['insc'] = insc
                hoy = datetime.now().date()
                ahora = (datetime.now() +  timedelta(minutes=30)).time() # RESTAR 30 MINUTOS
                hora = 0
                # if hoy.year - insc.fechanacimiento.year < 4:  SE QUITA LA VALIDACION SOLICITADO POR WC 22/07/2016
                if not IngresoGuarderia.objects.filter(detalle=insc,fechaentrada=hoy).exists():
                    # OCU en comentario por el momento 30-sep-2016
                    # if  insc.inscripcionguarderia.tipopersona.id == 2:
                    #     if insc.inscripcionguarderia.inscripcion.matriculado():
                    #         if insc.inscripcionguarderia.inscripcion.matricula_set.filter(nivel__periodo=periodo, nivel__cerrado=False).exists():
                    #             matricula = insc.inscripcionguarderia.inscripcion.matricula_set.filter(nivel__periodo=periodo, nivel__cerrado=False)[:1].get()
                    #             materias = matricula.materiaasignada_set.filter(materia__fin__gte=hoy,materia__inicio__lte=hoy).order_by('materia__inicio')
                    #             for  mat in  materias:
                    #                 if mat.materia.clase_set.filter(turno__comienza__lte=ahora , turno__termina__gte=ahora).exists():
                    #                     hora = mat.materia.clase_set.filter(turno__comienza__lte=ahora , turno__termina__gte=ahora)[:1].get()
                    #                 if hora:
                    #                     if hora.materia.clase_set.filter().exists() and mat.materia.clase_set.filter().exists() :
                    #                         if hora.materia.clase_set.filter()[:1].get().turno.termina <= mat.materia.clase_set.filter()[:1].get().materia.clase_set.filter()[:1].get().turno.termina:
                    #                             if mat.materia.clase_set.filter().exists():
                    #                                 hora= mat.materia.clase_set.filter()[:1].get()
                    #             # if hora:
                    #             #     data['form'] = RegistroGuarderiaForm(initial={"horaentrada": datetime.now().time() ,"horasalida":hora.materia.clase_set.filter()[:1].get().turno.termina })
                    #                 data['form'] = RegistroGuarderiaForm(initial={"horaentrada": datetime.now().time() ,"horasalida": datetime.now().time()   })
                    #                 return render(request ,"guarderia/registrar.html" ,  data)
                    #             else:
                    #
                    #                 data['form'] = RegistroGuarderiaForm(initial={"horaentrada": datetime.now().time() ,"horasalida": datetime.now().time()   })
                    #                 return render(request ,"guarderia/registrar.html" ,  data)
                    #         else:
                    #             return HttpResponseRedirect("guarderia?action=verdetalle&id="+str(insc.inscripcionguarderia.id)+"&info=No esta Matriculado en este periodo ")
                    #     else:
                    #         return HttpResponseRedirect("guarderia?action=verdetalle&id="+str(insc.inscripcionguarderia.id)+"&info=No esta Matriculado ")
                    # else:
                    #     data['form'] = RegistroGuarderiaForm(initial={"horaentrada": datetime.now().time() ,"horasalida": datetime.now().time()   })
                    #     return render(request ,"guarderia/registrar.html" ,  data)
                    data['form'] = RegistroGuarderiaForm(initial={"horaentrada": datetime.now().time() ,"horasalida": datetime.now().time()   })
                    return render(request ,"guarderia/registrar.html" ,  data)


                else:
                    return HttpResponseRedirect("guarderia?action=verdetalle&id="+str(insc.inscripcionguarderia.id)+"&info=Ya Se Encuentra Registrado En Este Dia")
                # else:
                #     return HttpResponseRedirect("guarderia?action=verdetalle&id="+str(insc.inscripcionguarderia.id)+"&info=Edad Superior a lo permitodo (3)")

        else:
            search = None
            if 's' in request.GET:
                search = request.GET['s']
            if search:
                inscripcion = InscripcionGuarderia.objects.filter(Q(inscripcion__persona__nombres__icontains=search) | Q(inscripcion__persona__apellido1__icontains=search) | Q(inscripcion__persona__apellido2__icontains=search) | Q(inscripcion__persona__cedula__icontains=search)).order_by('fecha') or InscripcionGuarderia.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search)).order_by('fecha')
            else:
                inscripcion = InscripcionGuarderia.objects.all().order_by('-fecha')
            paging = Paginator(inscripcion, 30)
            p=1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)
            data['paging'] = paging
            data['page'] = page
            data['search'] = search if search else ""
            data['inscripcion'] = page.object_list
            return render(request ,"guarderia/guarderia.html" ,  data)

