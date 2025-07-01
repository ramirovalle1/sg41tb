
from datetime import datetime
import json
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from decorators import secure_module
from sga.commonviews import addUserData, ip_client_address
from sga.models import TipoTest, PreguntaTest, ParametroTest, Persona, Inscripcion, InscripcionTipoTest, RespuestaTest, ResultadoRespuesta

__author__ = 'Manuel Flores'

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

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == "guardar":
                if "activo" in request.POST:
                    activo = True
                else:
                    activo = False

                if int(request.POST['editar'])==0:

                    tipotest = TipoTest(
                                        descripcion = str(request.POST['titulo']).upper(),
                                        descripcioncorta = str(request.POST['subtitulo']).upper(),
                                        observacion = str(request.POST['descripcion']).upper(),
                                        fecha = datetime.now().date(),
                                        estado = activo
                                        )
                    mensaje = 'Adicionando'
                else:
                    tipotest = TipoTest.objects.get(id=int(request.POST['editar']))
                    tipotest.tipotest=str(request.POST['titulo']).upper()
                    tipotest.descripcioncorta=str(request.POST['subtitulo']).upper()
                    tipotest.observacion=str(request.POST['descripcion']).upper()
                    tipotest.estado = activo

                    mensaje = 'Editado'

                tipotest.save()
                client_address = ip_client_address(request)
                #Log de ADICIONAR TEST
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(tipotest).pk,
                    object_id       = tipotest.id,
                    object_repr     = force_str(tipotest),
                    action_flag     = ADDITION,
                    change_message  = mensaje+' TEST (' + client_address + ')'+mensaje)

                return HttpResponseRedirect('/admintest')

            elif action == 'guardarpreg':
                idtest = int(request.POST['idtest'])
                tipotest = TipoTest.objects.get(id=idtest)
                pregunta = request.POST['pregunta']
                numero = request.POST['numero']
                if "activo" in request.POST:
                    activo = True
                else:
                    activo = False

                preguntatest = PreguntaTest(
                                    tipotest = tipotest,
                                    pregunta = pregunta,
                                    estado=activo,
                                    orden=numero
                                    )
                preguntatest.save()
                client_address = ip_client_address(request)
                #Log de ADICIONAR INSCRIPCION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(preguntatest).pk,
                    object_id       = preguntatest.id,
                    object_repr     = force_str(preguntatest),
                    action_flag     = ADDITION,
                    change_message  = 'Adicionado Pregunta (' + client_address + ')')

                return HttpResponseRedirect('/admintest?action=verpregunta&id='+str(idtest))

            elif action == 'editarpreg':

                idpregunta = int(request.POST['idpregunexamen'])
                idtest = int(request.POST['idtest'])
                tipotest = TipoTest.objects.get(id=idtest)
                pregunta = request.POST['pregunta']
                numero = request.POST['numero']
                if "activo" in request.POST:
                    activo = True
                else:
                    activo = False

                preguntest=PreguntaTest.objects.get(id=idpregunta,tipotest=tipotest)
                preguntest.pregunta=pregunta
                preguntest.orden=numero
                preguntest.estado=activo

                preguntest.save()
                client_address = ip_client_address(request)
                #Log de ADICIONAR INSCRIPCION
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(preguntest).pk,
                    object_id       = preguntest.id,
                    object_repr     = force_str(preguntest),
                    action_flag     = CHANGE,
                    change_message  = 'EDITADA PREGUNTA (' + client_address + ')')

                return HttpResponseRedirect('/admintest?action=verpregunta&id='+str(idtest))

            elif action == 'ingresarparametro':
                 idtest = int(request.POST['idtest'])
                 tipotest = TipoTest.objects.get(id=idtest)
                 if "activo" in request.POST:
                    activo = True
                 else:
                    activo = False
                 parametrotes = ParametroTest(descripcion=request.POST['txtdescricpion'],
                                              puntaje=request.POST['puntaje'],tipotest=tipotest,estado=activo)
                 parametrotes.save()

                 return HttpResponseRedirect('/admintest?action=verparametros&id='+str(idtest))

            elif action == 'editarparametro':
                 idtest = int(request.POST['idtest'])
                 tipotest = TipoTest.objects.get(id=idtest)
                 if "activo" in request.POST:
                    activo = True
                 else:
                    activo = False
                 parametrotes = ParametroTest(descripcion=request.POST['txtdescricpion'],
                                              puntaje=request.POST['puntaje'],tipotest=tipotest,estado=activo)
                 parametrotes.save()

                 return HttpResponseRedirect('/admintest?action=verparametros&id='+str(idtest))


            elif action=="guardarespuesta":
                 try:
                    user=request.user
                    persona=Persona.objects.get(usuario=user)
                    inscrip= Inscripcion.objects.get(persona=persona)
                    tipotest = TipoTest.objects.filter(id=int(request.POST['idtest']))[:1].get()
                    inscriptest= InscripcionTipoTest.objects.get(inscripcion=inscrip,tipotest=tipotest)
                    pregunta = PreguntaTest.objects.get(id=int(request.POST['idpregunta']))

                    if ParametroTest.objects.filter(id=int(request.POST['idrespuesta'])).exists():
                        parametro= ParametroTest.objects.get(id=int(request.POST['idrespuesta']))
                        if not RespuestaTest.objects.filter(tipotest=tipotest,inscripciontipotest=inscriptest,preguntatest=pregunta).exists():
                            respuesta= RespuestaTest(inscripciontipotest=inscriptest,tipotest=tipotest,preguntatest=pregunta,respuesta=parametro.puntaje,parametrotest=parametro)
                            respuesta.save()
                        else:
                            respuesta=RespuestaTest.objects.get(tipotest=tipotest,inscripciontipotest=inscriptest,preguntatest=pregunta)
                            respuesta.parametrotest=parametro
                            respuesta.respuesta=parametro.puntaje
                            respuesta.save()
                    else:
                        respuesta=RespuestaTest.objects.get(tipotest=tipotest,inscripciontipotest=inscriptest,preguntatest=pregunta)
                        respuesta.parametrotest=None
                        respuesta.respuesta=0
                        respuesta.save()

                    #pregunta = PreguntaTest.objects.filter(tipotest=tipotest).order_by('orden')
                    #data['listaparametros'] = ParametroTest.objects.filter(tipotest=tipotest)
                    #data['tipotest']=tipotest
                    #data['lispregunta'] = pregunta
                    return HttpResponse(json.dumps({'result': 'ok'}), content_type="application/json")
                 except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad','message': str(e)}), content_type="application/json")







        else:
            data = {'title':'Administrar Test'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']

                if action == "verpregunta":
                    data['title'] = 'Ver Preguntas'
                    tipotest = TipoTest.objects.filter(id=int(request.GET['id']))[:1].get()

                    data['registrotest'] = tipotest
                    preguntaexterno = PreguntaTest.objects.filter(tipotest=tipotest).order_by('orden')

                    paging = MiPaginador(preguntaexterno, 10)
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
                    data['idtipotes']=tipotest.id

                    data['lispregunta'] = page.object_list
                    return render(request ,"testconduccion/verpreguntas.html" ,  data)


                if action == 'activa':
                   tipotest =  TipoTest.objects.filter(id=request.GET['id'])[:1].get()

                   if tipotest.estado:
                      activo = False
                      mensaje = 'Desactivacion de Examen'
                   else:
                       activo = True
                       mensaje = 'Activacion de Examen'
                   tipotest.estado = activo
                   tipotest.save()

                   client_address = ip_client_address(request)
                   #Log de ADICIONAR INSCRIPCION
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(tipotest).pk,
                        object_id       = tipotest.id,
                        object_repr     = force_str(tipotest),
                        action_flag     = CHANGE,
                        change_message  = mensaje +' TEST  (' + client_address + ')')
                   return HttpResponseRedirect('/admintest')

                elif action == 'eliminpreg':
                   preguntest=PreguntaTest.objects.get(id=request.GET['id'])
                   preguntest.delete()
                   client_address = ip_client_address(request)
                   #Log de ADICIONAR INSCRIPCION
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(preguntest).pk,
                        object_id       = preguntest.id,
                        object_repr     = force_str(preguntest),
                        action_flag     = DELETION,
                        change_message  = 'Eliminacion de pregunta  (' + client_address + ')')

                   return HttpResponseRedirect('/admintest?action=verpregunta&id='+str(preguntest.tipotest.id))

                elif action == "eliminartest":
                    tipotest =  TipoTest.objects.filter(id=request.GET['id'])[:1].get()
                    tipotest.delete()
                    return HttpResponseRedirect('/admintest')

                elif action == "verparametros":
                        data['title'] = 'Ver Parametros'
                        tipotest = TipoTest.objects.filter(id=request.GET['id'])[:1].get()
                        data['idtipotes']=tipotest.id
                        data['listaparametros'] = ParametroTest.objects.filter(tipotest=tipotest)
                        return render(request ,"testconduccion/adminparametros.html" ,  data)

                elif action=="eliminparametro":
                   parametro=ParametroTest.objects.get(id=int(request.GET['id']))
                   parametro.delete()
                   client_address = ip_client_address(request)
                   #Log de ADICIONAR INSCRIPCION
                   LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(parametro).pk,
                        object_id       = parametro.id,
                        object_repr     = force_str(parametro),
                        action_flag     = DELETION,
                        change_message  = 'Eliminacion de parametro  (' + client_address + ')')

                   return HttpResponseRedirect('/admintest?action=verparametros&id='+str(parametro.tipotest_id))

                elif action=="test":
                    user=request.user
                    persona=Persona.objects.get(usuario=user)
                    inscrip= Inscripcion.objects.get(persona=persona)
                    tipotestid= InscripcionTipoTest.objects.filter(inscripcion__id=inscrip.id,estado=True).values('tipotest_id')
                    tipotest = TipoTest.objects.filter(estado=True).exclude(id__in=tipotestid)
                    #tipotest = TipoTest.objects.filter(id=tipotestid)
                    data['tipotest'] = tipotest
                    return render(request ,"testconduccion/listatest.html" ,  data)

                elif action=="inicatest":
                    data['title'] = ''
                    usuario=request.user
                    persona=Persona.objects.get(usuario=usuario)
                    inscrip= Inscripcion.objects.get(persona=persona)
                    tipotest = TipoTest.objects.filter(id=int(request.GET['id']))[:1].get()
                    if not InscripcionTipoTest.objects.filter(inscripcion=inscrip,tipotest=tipotest).exists():
                        inscriptest = InscripcionTipoTest(inscripcion=inscrip,tipotest=tipotest,observacion=tipotest.descripcion,fechainicio=datetime.now())
                        inscriptest.save()
                    if  'info' in request.GET:
                        data['mensajeerror']='No puede finzalizar porque no ha completado el test'
                    if  tipotest.estado:
                        data['inscipciontipotest']=InscripcionTipoTest.objects.get(inscripcion=inscrip,tipotest=tipotest)
                        data['registrotest'] = tipotest
                        pregunta = PreguntaTest.objects.filter(tipotest=tipotest).order_by('orden')
                        data['listaparametros'] = ParametroTest.objects.filter(tipotest=tipotest)
                        data['tipotest']=tipotest
                        data['lispregunta'] = pregunta
                        data['inscipcion'] = inscrip
                        return render(request ,"testconduccion/test.html" ,  data)
                    else:
                        return render(request ,"testconduccion/listatest.html" ,  data)

                elif action=="guardarespuesta":
                    user=request.user
                    persona=Persona.objects.get(usuario=user)
                    inscrip= Inscripcion.objects.get(persona=persona)
                    tipotest = TipoTest.objects.filter(id=int(request.GET['idtest']))[:1].get()
                    inscriptest= InscripcionTipoTest.objects.get(inscripcion=inscrip,tipotest=tipotest)
                    pregunta = PreguntaTest.objects.get(id=int(request.GET['idpregunta']))
                    parametro= ParametroTest.objects.get(id=int(request.GET['idrespuesta']))
                    if not RespuestaTest.objects.filter(tipotest=tipotest,inscripciontipotest=inscriptest,preguntatest=pregunta).exists():
                        respuesta= RespuestaTest(inscripciontipotest=inscriptest,tipotest=tipotest,preguntatest=pregunta,respuesta=parametro.puntaje,parametrotest=parametro)
                        respuesta.save()
                    else:
                        respuesta=RespuestaTest.objects.get(tipotest=tipotest,inscripciontipotest=inscriptest,preguntatest=pregunta)
                        respuesta.parametrotest=parametro
                        respuesta.respuesta=parametro.puntaje
                        respuesta.save()

                    pregunta = PreguntaTest.objects.filter(tipotest=tipotest).order_by('orden')
                    data['listaparametros'] = ParametroTest.objects.filter(tipotest=tipotest)
                    data['tipotest']=tipotest
                    data['lispregunta'] = pregunta
                    return render(request ,"testconduccion/test.html" ,  data)

                elif action == 'finalizartest':
                    idtest = int(request.GET['idtest'])
                    test= TipoTest.objects.get(id=idtest)
                    if PreguntaTest.objects.filter(tipotest=test).count()!= RespuestaTest.objects.filter(tipotest=test,inscripciontipotest__inscripcion__id=request.GET['idinscrip']).count():



                        return HttpResponseRedirect("/admintest?action=inicatest&info=No puede finzalizar porque no ha completado el test&id="+str(idtest))
                    else:
                        user=request.user
                        persona=Persona.objects.get(usuario=user)
                        inscrip= Inscripcion.objects.get(id=request.GET['idinscrip'])
                        inscriptest= InscripcionTipoTest.objects.get(inscripcion=inscrip,tipotest=test)
                        inscriptest.horafin=datetime.now()
                        inscriptest.estado=True
                        inscriptest.save()
                        result=0
                        for a in RespuestaTest.objects.filter(tipotest=test,inscripciontipotest__inscripcion=inscrip):
                            result=int(result)+int(a.respuesta)

                        if not ResultadoRespuesta.objects.filter(inscripciontipotest=inscriptest,tipotest=test).exists():
                            resultado = ResultadoRespuesta(inscripciontipotest=inscriptest,tipotest=test,puntaje=result)
                            resultado.save()
                        else:
                            resultado = ResultadoRespuesta.objects.filter(inscripciontipotest=inscriptest,tipotest=test,puntaje=result)
                            resultado.puntaje=result
                            resultado.save()

                        tipotestid= InscripcionTipoTest.objects.filter(inscripcion__id=request.GET['idinscrip'],estado=True).values('tipotest_id')
                        tipotest = TipoTest.objects.filter(estado=True).exclude(id__in=tipotestid)
                        data['tipotest'] = tipotest
                        if tipotest.count()>0:
                            return render(request ,"testconduccion/listatest.html" ,  data)
                        else:
                            return HttpResponseRedirect('/')

                elif action == 'veresultado':
                    idtest = int(request.GET['id'])
                    test= TipoTest.objects.get(id=idtest)
                    listaresultado= ResultadoRespuesta.objects.filter(tipotest=test)

                    data['listaresultado'] = listaresultado

                    return render(request ,"testconduccion/veresultado.html" ,  data)







            else:

                tipotest = TipoTest.objects.filter()
                data['tipotest'] = tipotest
                return render(request ,"testconduccion/admintest.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect('/?info='+str(ex))
