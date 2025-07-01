from datetime import datetime
import json
from django.contrib.admin.models import LogEntry,CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import ASIGNATURA_PRACTICA_CONDUCCION
from sga.commonviews import addUserData, ip_client_address
from sga.forms import SolicitudSecretariaDocenteForm, AlumnoPracticaForm
from sga.models import SolicitudSecretariaDocente,AlumnoPractica, SesionPractica, Practica,Inscripcion,ClaseConduccion,Periodo,GrupoPractica,TurnoPractica,Persona, MateriaAsignada, Matricula, Materia, Asignatura, ProfesorMateria


@login_required(redirect_field_name='ret', login_url='/login')
# @secure_module
def view(request):
    data = {'title': 'Practicas de Conduccion'}
    addUserData(request, data)
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action=='guardar':
                f = AlumnoPracticaForm(request.POST)
                inscripcion = Inscripcion.objects.get(persona=request.POST['persona'])
                if f.is_valid():
                    alumnoprac = AlumnoPractica(claseconduccion=f.cleaned_data['claseconduccion'],
                                    inscripcion=inscripcion)
                    alumnoprac.save()
                    matricula = Matricula.objects.filter(inscripcion=inscripcion).order_by('-id')[:1].get()
                    a = Asignatura.objects.get(pk=ASIGNATURA_PRACTICA_CONDUCCION)
                    hoy = datetime.today().date()
                    # if Materia.objects.filter(asignatura=a,nivel=matricula.nivel).exists():
                    #     materia = Materia.objects.filter(asignatura=a,nivel=matricula.nivel)[:1].get()
                    # else:
                    materia = Materia(asignatura=a,
                                      nivel=matricula.nivel,
                                      horas=32,
                                      creditos=3,
                                      identificacion=a.codigo,
                                      fin=hoy)
                    materia.save()
                    pmateria = ProfesorMateria(materia=materia,
                                               profesor=alumnoprac.claseconduccion.profesor,
                                               desde = alumnoprac.claseconduccion.practica.fechainicio,
                                               hasta = alumnoprac.claseconduccion.practica.fechafin)
                    pmateria.save()


                    asign = MateriaAsignada(matricula=matricula,materia=materia,notafinal=0,asistenciafinal=0,supletorio=0)
                    asign.save()

                    #Obtain client ip address
                    client_address = ip_client_address(request)

                    # Log de EDITAR HORARIO CLASE
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(alumnoprac).pk,
                        object_id       = alumnoprac.id,
                        object_repr     = force_str(alumnoprac),
                        action_flag     = CHANGE,
                        change_message  = 'Modificado Horario Clase (' + client_address + ')'  )
                    return HttpResponseRedirect("/inscripciones")
                else:
                    return HttpResponseRedirect("/alumnopractica")
            elif action=='practica':
                if GrupoPractica.objects.filter(pk=request.POST['id']).exists():
                    grupo = GrupoPractica.objects.filter(pk=request.POST['id'])
                    fecha=datetime.date(datetime.now())
                    practica = Practica.objects.filter(grupopracticas=grupo,fechafin__gte=fecha)[:1].get()
                    result={}
                    result['practica'] = practica
                    result['result']  = "ok"
                    return HttpResponse(json.dumps(result),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
    else:
        try:
            data = {'title': 'Practicas de Conduccion'}
            addUserData(request, data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='practica':
                    data={}
                    if GrupoPractica.objects.filter(pk=request.GET['id']).exists():
                        grupo = GrupoPractica.objects.get(pk=request.GET['id'])
                        # fecha=datetime.date(datetime.now())
                        # ?practica = Practica.objects.filter(grupopracticas=grupo,fechafin__gte=fecha)

                        form = AlumnoPracticaForm(initial={'grupopractica': GrupoPractica.objects.get(pk=request.GET['id'])})
                        fecha=datetime.date(datetime.now())
                        form.for_practica(grupo,fecha,request.session['periodo'])
                        data['form'] = form
                        data['persona'] = Persona.objects.get(pk=request.GET['persona'])
                        return render(request ,"alumnopractica/alumnopractica.html" ,  data)
                elif action=='turno':
                    practica = Practica.objects.get(pk=request.GET['id'])
                    grupo = practica.grupopracticas.id
                    sesiondia=practica.grupopracticas.sesionpracticas.diasemana()
                    form = AlumnoPracticaForm(initial={'grupopractica': GrupoPractica.objects.get(pk=grupo),'practica': Practica.objects.get(pk=request.GET['id'])})
                    fecha=datetime.date(datetime.now())
                    form.for_turno(practica,grupo,fecha,request.session['periodo'],sesiondia)
                    data['form'] = form
                    data['persona'] = Persona.objects.get(pk=request.GET['persona'])
                    return render(request ,"alumnopractica/alumnopractica.html" ,  data)
                elif action == 'ingreso':
                    data = {'title': 'Practica Conduccion'}
                    addUserData(request,data)
                    inscripcion = Inscripcion.objects.get(pk=request.GET['id'])
                    if not AlumnoPractica.objects.filter(inscripcion=inscripcion,claseconduccion__practica__grupopracticas__periodo=request.session['periodo'] ).exists():
                        data={}
                        form = AlumnoPracticaForm()
                        # data['form'] = PersonaForm(instance=persona)
                        data['periodo'] = Periodo.objects.get(pk=request.session['periodo'].id)
                        form.for_claseconduc(request.session['periodo'])
                        data['form']=form
                        data['persona'] = Persona.objects.get(pk=inscripcion.persona.id)
                        return render(request ,"alumnopractica/alumnopractica.html" ,  data)
                    else:
                        data={}
                        alumnopractica = AlumnoPractica.objects.filter(inscripcion=inscripcion,claseconduccion__practica__grupopracticas__periodo=request.session['periodo'])[:1].get()
                        data['semana'] = ['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado','Domingo']
                        data['alumnopractica'] =alumnopractica
                        if GrupoPractica.objects.filter(pk=alumnopractica.claseconduccion.practica.grupopracticas.id,periodo=request.session['periodo']).exists():
                            data['nivel'] =GrupoPractica.objects.filter(pk=alumnopractica.claseconduccion.practica.grupopracticas.id,periodo=request.session['periodo'])[:1].get()
                            data['clases'] = ClaseConduccion.objects.filter(turnopractica=alumnopractica.claseconduccion.turnopractica,profesor=alumnopractica.claseconduccion.profesor,practica=alumnopractica.claseconduccion.practica)
                            data['turnos'] = TurnoPractica.objects.filter(pk=alumnopractica.claseconduccion.turnopractica.id).order_by('turno')
                            data['periodo'] = Periodo.objects.get(pk=request.session['periodo'].id)
                            data['ingr'] = 1
                            return render(request ,"alumnopractica/horariobs.html" ,  data)

                else:
                    return HttpResponseRedirect("/")

        except:
            return HttpResponseRedirect("/")
        else:
            persona = request.session['persona']
            if Inscripcion.objects.filter(persona=persona).exists():
                insc= Inscripcion.objects.filter(persona=persona)[:1].get()
                if  AlumnoPractica.objects.filter(inscripcion=insc,claseconduccion__practica__grupopracticas__periodo=request.session['periodo']).exists():
                    data={}
                    alumnopractica = AlumnoPractica.objects.filter(inscripcion=insc,claseconduccion__practica__grupopracticas__periodo=request.session['periodo'])[:1].get()
                    data['semana'] = ['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado','Domingo']
                    data['alumnopractica'] =alumnopractica
                    data['nivel'] =GrupoPractica.objects.filter(pk=alumnopractica.claseconduccion.practica.grupopracticas.id,periodo=request.session['periodo'])[:1].get()
                    data['clases'] = ClaseConduccion.objects.filter(turnopractica=alumnopractica.claseconduccion.turnopractica,profesor=alumnopractica.claseconduccion.profesor,practica=alumnopractica.claseconduccion.practica)
                    data['turnos'] = TurnoPractica.objects.filter(pk=alumnopractica.claseconduccion.turnopractica.id).order_by('turno')
                    data['periodo'] = Periodo.objects.get(pk=request.session['periodo'].id)
                    data['ingr'] = 2
                    return render(request ,"alumnopractica/horariobs.html" ,  data)
                else:
                    return HttpResponseRedirect("/?info=NO TIENE HORARIO DE PRACTICA")

            else:
                return HttpResponseRedirect("/")