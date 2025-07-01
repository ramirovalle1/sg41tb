from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from settings import NOTA_PARA_SUPLET, NOTA_PARA_APROBAR, PUNTAJE_MIN_EXAMEN, NUM_PREGUN_EXAMENPARC, NUM_PREGUN_EXAMENPARCSUPLE
from sga.commonviews import addUserData, ip_client_address
from sga.models import Profesor, ProfesorMateria, Nivel, Asignatura, TituloExamenParcial, ExamenParcial, MateriaAsignada, ExamenParRespuesta, DetActivaExamenParc, PreguntaAsignatura


class MiPaginador(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador,self).__init__(object_list, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left<1:
            left=1
        if right>self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right+1)
        self.primera_pagina = True if left>1 else False
        self.ultima_pagina = True if right<self.num_pages else False
        self.ellipsis_izquierda = left-1
        self.ellipsis_derecha = right+1

__author__ = 'User'
@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == "guardar":
                if "supletorio" in request.POST:
                    supletorio = True
                else:
                    supletorio = False
                tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(request.POST['tiempo'].split(':')[0]),int(request.POST['tiempo'].split(':')[1]))

                if request.POST['editar'] == '0':
                    if supletorio:
                        numeropregunta = NUM_PREGUN_EXAMENPARCSUPLE
                    else:
                        numeropregunta =  NUM_PREGUN_EXAMENPARC
                    profesormate = ProfesorMateria.objects.get(id=request.POST['profemateid'])
                    if PreguntaAsignatura.objects.filter(asignatura=profesormate.materia.asignatura,carrera=profesormate.materia.nivel.carrera).count() < numeropregunta:
                        return HttpResponseRedirect('/proexamenparcial?fp=1')
                    tituloexamenparcial = TituloExamenParcial(
                                        tituloexamen = request.POST['titulo'],
                                        profesormateria_id = request.POST['profemateid'],
                                        subtituloexamen = request.POST['subtitulo'],
                                        descripcion = request.POST['descripcion'],
                                        fecha = datetime.now(),
                                        tiempo = tiempo,
                                        supletorio = supletorio,
                                        usuario=request.user)
                    mensaje = 'Adicionando'
                else:
                    tituloexamenparcial = TituloExamenParcial.objects.filter(id=request.POST['editar'])[:1].get()
                    tituloexamenparcial.profesormateria_id = request.POST['profemateid']
                    tituloexamenparcial.tituloexamen = request.POST['titulo']
                    tituloexamenparcial.subtituloexamen = request.POST['subtitulo']
                    tituloexamenparcial.descripcion = request.POST['descripcion']
                    tituloexamenparcial.fecha = datetime.now()
                    tituloexamenparcial.tiempo = tiempo
                    tituloexamenparcial.supletorio = supletorio
                    tituloexamenparcial.usuario=request.user
                    mensaje = 'Editando'
                tituloexamenparcial.save()
                client_address = ip_client_address(request)
                #Log de ADICIONAR INSCRIPCION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(tituloexamenparcial).pk,
                    object_id       = tituloexamenparcial.id,
                    object_repr     = force_str(tituloexamenparcial),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' examen (' + client_address + ')')
                return HttpResponseRedirect('/proexamenparcial')
            elif action == 'guardvalida':
                try:
                    examenparcial = ExamenParcial.objects.get(id=request.POST['idexam'])
                    materiaasignada = MateriaAsignada.objects.filter(materia=examenparcial.tituloexamenparcial.profesormateria.materia,matricula=examenparcial.matricula).order_by()[:1].get()
                    evaluacion = materiaasignada.evaluacion()
                    if request.POST['activ'] == 'True':
                        activo = False
                        mensaje = 'Desactivando examen parcial'
                        if not examenparcial.tituloexamenparcial.supletorio:
                            evaluacion.examen = 0
                        if examenparcial.tituloexamenparcial.supletorio:
                            evaluacion.recuperacion = 0
                    else:
                        activo = True
                        mensaje = 'Activando examen parcial'
                        if not examenparcial.tituloexamenparcial.supletorio:
                            evaluacion.examen = int(examenparcial.puntaje)
                        if examenparcial.tituloexamenparcial.supletorio:
                            evaluacion.recuperacion = int(examenparcial.puntaje)
                        for e in ExamenParcial.objects.filter(matricula=examenparcial.matricula,tituloexamenparcial=examenparcial.tituloexamenparcial,valida=True):
                            e.valida = False
                            e.save()
                    examenparcial.valida = activo
                    examenparcial.save()
                    if examenparcial.finalizado:
                        evaluacion.save()
                        evaluacion.actualiza_estado()
                    detactiva = DetActivaExamenParc(examenparcial = examenparcial,
                                        observacion = request.POST['obs'],
                                        usuario = request.user,
                                        fecha = datetime.now(),
                                        activo = activo)
                    detactiva.save()
                    client_address = ip_client_address(request)
                    #Log de ADICIONAR INSCRIPCION
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(detactiva).pk,
                        object_id       = detactiva.id,
                        object_repr     = force_str(detactiva),
                        action_flag     = ADDITION,
                        change_message  = mensaje+' examen (' + client_address + ')')
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad","mensaje":str(ex)}),content_type="application/json")
        else:
            data = {'title':'Examenes Parciales'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'activa':
                   tituloexamenparcial =  TituloExamenParcial.objects.filter(id=request.GET['id'])[:1].get()

                   if tituloexamenparcial.activo:
                      if ExamenParcial.objects.filter(tituloexamenparcial=tituloexamenparcial,valida=True,finalizado=True).count() != ExamenParcial.objects.filter(tituloexamenparcial = tituloexamenparcial,valida=True).count():
                          return HttpResponseRedirect('/proexamenparcial?info=Faltan examenes por finalizar')
                      activo = False
                      mensaje = 'Desactivacion de Examen'
                   else:
                       activo = True
                       mensaje = 'Activacion de Examen'
                   tituloexamenparcial.activo = activo
                   tituloexamenparcial.save()

                   client_address = ip_client_address(request)
                   #Log de ADICIONAR INSCRIPCION
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tituloexamenparcial).pk,
                        object_id       = tituloexamenparcial.id,
                        object_repr     = force_str(tituloexamenparcial),
                        action_flag     = ADDITION,
                        change_message  = mensaje +' de parcial  (' + client_address + ')')
                   return HttpResponseRedirect('/proexamenparcial')

                elif action == "deltitut":
                    tituloexamenparcial = TituloExamenParcial.objects.filter(id=request.GET['id'])[:1].get()
                    tituloexamenparcial.delete()
                    return HttpResponseRedirect('/proexamenparcial')

                elif action == "verexam":
                    examenpar = ExamenParcial.objects.filter(id=request.GET['idexa'])[:1].get()
                    examenparcial = ExamenParcial.objects.filter(tituloexamenparcial=examenpar.tituloexamenparcial,matricula=examenpar.matricula)
                    data['examenparcial'] = examenparcial
                    data['tituloexamenparcial'] = examenpar.tituloexamenparcial
                    return render(request ,"examenparcial/detalleexamen.html" ,  data)
                elif action == "examen":
                    examenparcial = ExamenParcial.objects.filter(id=request.GET['id'])[:1].get()
                    examenparrespuesta = ExamenParRespuesta.objects.filter(examenparcial=examenparcial)
                    data['examenparcial'] = examenparcial
                    data['tituloexamenparcial'] = examenparcial.tituloexamenparcial
                    if examenparcial.tituloexamenparcial.supletorio:
                        numeropregunta = NUM_PREGUN_EXAMENPARCSUPLE
                    else:
                        numeropregunta =  NUM_PREGUN_EXAMENPARC
                    paging = MiPaginador(examenparrespuesta, numeropregunta)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)
                    data['paging'] = paging
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['preguntaexamen'] = page.object_list
                    data['examenparcial'] = examenparcial
                    data['NOTA_PARA_APROBAR'] = NOTA_PARA_APROBAR
                    data['NOTA_PARA_SUPLET'] = NOTA_PARA_SUPLET

                    return render(request ,"examenparcial/verexamen.html" ,  data)

                elif action == "verinscr":
                    tituloexamenparcial = TituloExamenParcial.objects.get(id=request.GET['id'])
                    if MateriaAsignada.objects.filter(materia=tituloexamenparcial.profesormateria.materia).exists():
                        search = ''
                        if 'idexa' in request.GET:
                            data['idexa'] = request.GET['idexa']
                        if 's' in request.GET:
                            search = request.GET['s']
                            data['search'] = request.GET['s']
                        if search:
                            ss = search.split(' ')
                            while '' in ss:
                                ss.remove('')
                            if len(ss)==1:
                                materiaasignada = MateriaAsignada.objects.filter(Q(materia=tituloexamenparcial.profesormateria.materia), Q(Q(matricula__inscripcion__persona__nombres__icontains=search) | Q(matricula__inscripcion__persona__apellido1__icontains=search) | Q(matricula__inscripcion__persona__apellido2__icontains=search) | Q(matricula__inscripcion__persona__cedula__icontains=search) | Q(matricula__inscripcion__persona__pasaporte__icontains=search))).order_by('matricula__inscripcion__persona__apellido1', 'matricula__inscripcion__persona__apellido2')
                            else:
                                materiaasignada = MateriaAsignada.objects.filter(Q(materia=tituloexamenparcial.profesormateria.materia), Q(Q(matricula__inscripcion__persona__apellido1__icontains=ss[0]) & Q(matricula__inscripcion__persona__apellido2__icontains=ss[1]))).order_by('matricula__inscripcion__persona__apellido1','matricula__inscripcion__persona__apellido2','matricula__inscripcion__persona__nombres')
                        else:
                            materiaasignada = MateriaAsignada.objects.filter(materia=tituloexamenparcial.profesormateria.materia).order_by('matricula__inscripcion__persona__apellido1', 'matricula__inscripcion__persona__apellido2')
                        paging = MiPaginador(materiaasignada, 10)
                        p = 1
                        try:
                            if 'page' in request.GET:
                                p = int(request.GET['page'])
                            page = paging.page(p)
                        except:
                            page = paging.page(1)
                        data['paging'] = paging
                        data['rangospaging'] = paging.rangos_paginado(p)
                        data['page'] = page
                        data['numpag'] = p
                        data['materiaasignadas'] = page.object_list
                        data['materiaasignadas'] = page.object_list
                        data['materiaasignadas'] = page.object_list
                    data['tituloexamenparcial'] = tituloexamenparcial
                    data['NOTA_PARA_SUPLET'] = NOTA_PARA_SUPLET
                    data['NOTA_PARA_APROBAR'] = NOTA_PARA_APROBAR
                    data['PUNTAJE_MIN_EXAMEN'] = PUNTAJE_MIN_EXAMEN
                    data['titulosexamenes'] = TituloExamenParcial.objects.filter(profesormateria__profesor=tituloexamenparcial.profesormateria.profesor)
                    return render(request ,"examenparcial/matriculamateria.html" ,  data)
            else:
                asign = ''
                nivel = ''
                profesor = Profesor.objects.filter(persona=data['persona'])[:1].get()
                profesormateria = ProfesorMateria.objects.filter(profesor=profesor)
                idnivel = TituloExamenParcial.objects.filter(profesormateria__profesor=profesor).values('profesormateria__materia__nivel').distinct('profesormateria__materia__nivel')
                niveles = Nivel.objects.filter(id__in=idnivel)
                asignaturas = Asignatura.objects.filter(id__in=profesormateria.values('materia__asignatura'))

                data['profesormateria'] = ProfesorMateria.objects.filter(profesor=profesor,materia__cerrado=False).order_by('materia__nivel')

                if 'asign' in request.GET:
                    asign = Asignatura.objects.get(id=request.GET['asign'])
                    data['asign'] = asign
                if 'info' in request.GET:
                    data['info'] = request.GET['info']
                if 'fp' in request.GET:
                    data['info'] = 'La asignatura no tiene las preguntas minimas para crear el examen'
                if 'niv' in request.GET:
                    nivel = Nivel.objects.get(id=request.GET['niv'])
                    data['niv'] = nivel
                if asign and nivel:
                    tituloexamenparcial = TituloExamenParcial.objects.filter(profesormateria__profesor=profesor,profesormateria__materia__nivel=nivel,
                                                                             profesormateria__materia__asignatura=asign)
                elif asign:
                    tituloexamenparcial = TituloExamenParcial.objects.filter(profesormateria__profesor=profesor,profesormateria__materia__asignatura=asign)
                elif nivel:
                    tituloexamenparcial = TituloExamenParcial.objects.filter(profesormateria__profesor=profesor,profesormateria__materia__nivel=nivel)
                else:
                    tituloexamenparcial = TituloExamenParcial.objects.filter(profesormateria__profesor=profesor)
                paging = MiPaginador(tituloexamenparcial, 10)
                p = 1
                try:
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    page = paging.page(p)
                except:
                    page = paging.page(1)
                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['numpag'] = p
                data['asignaturas'] = asignaturas
                data['niveles'] = niveles

                data['tituloexamenparcial'] = page.object_list
                return render(request ,"examenparcial/profe_examenparcial.html" ,  data)
    except Exception as e:
        print(e)
        return HttpResponseRedirect('/?info=Error en excepcion comuniquese con el administrador')
