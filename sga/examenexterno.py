from datetime import datetime, timedelta
import json
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from settings import DEFAULT_PASSWORD, NUMERO_PREGUNTA_EXTERNO, NOTA_PARA_EXAMEN_EXTERNO, EXAMEN_EXTERNO_INGRESO, TIPO_AULA, ID_GRUPO_EXAMEN_CASADE
from sga.commonviews import addUserData, ip_client_address
from sga.models import RubroEspecieValorada, PersonaExamenExt, PersonaExterna, ExamenExterno, PreguntaExterno, DetalleExamenExt, RespuestaExterno, Aula, Inscripcion, ComponenteExamen

__author__ = 'jurgiles'
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
def view(request):
    try:
        if request.method == 'POST':
            action = request.POST['action']
            if action == "consultespecie":
                try:
                    fecha = datetime.now().date() + timedelta(days=-20)
                    pasaporte = 'false'
                    numdoc = ''
                    nombres = ''
                    existe = False
                    idpersonaexter = 0

                    if RubroEspecieValorada.objects.filter(serie=request.POST['especie'],rubro__cancelado=True,rubro__fecha__gte=fecha).exists():
                        especie =  RubroEspecieValorada.objects.filter(serie=request.POST['especie'],rubro__cancelado=True,rubro__fecha__gte=fecha)[:1].get()
                        if PersonaExamenExt.objects.filter(especie= especie,examenexterno=None).exists() or not PersonaExamenExt.objects.filter(especie= especie).exists() :

                            if PersonaExamenExt.objects.filter(especie= especie,examenexterno=None).exists():
                                personaexamenext = PersonaExamenExt.objects.filter(especie= especie,examenexterno=None)[:1].get()
                                existe = True if PersonaExamenExt.objects.filter(personaextern=personaexamenext.personaextern).exclude(examenexterno=None).exists() else False
                                if personaexamenext.personaextern.pasaporte:
                                    pasaporte = 'true'
                                numdoc = personaexamenext.personaextern.numdocumento
                                nombres = personaexamenext.personaextern.nombres
                                idpersonaexter = personaexamenext.personaextern.id
                            return HttpResponse(json.dumps({"result":"ok",'especieid':str(especie.id),'idpersonaexter':str(idpersonaexter),'pasaporte':str(pasaporte),'numdoc':numdoc,'nombres':nombres,"existe":existe}),content_type="application/json")
                        elif not PersonaExamenExt.objects.filter(especie= especie,finalizado=False).exists():
                            return HttpResponse(json.dumps({"result":"finalizado",'especieid':str(especie.id)}),content_type="application/json")

                        personaexamenext = PersonaExamenExt.objects.filter(especie= especie,finalizado=False).exclude(examenexterno=None)[:1].get()
                        existe = True if PersonaExamenExt.objects.filter(personaextern=personaexamenext.personaextern).exclude(examenexterno=None).exists() else False
                        if personaexamenext.personaextern.pasaporte:
                            pasaporte = 'true'
                        numdoc = personaexamenext.personaextern.numdocumento
                        nombres = personaexamenext.personaextern.nombres
                        idpersonaexter = personaexamenext.id
                        return HttpResponse(json.dumps({"result":"continuaexa",'descripcionexa':str(personaexamenext.examenexterno.descripcion),'idexamenext':str(personaexamenext.examenexterno.id),'especieid':str(especie.id),'idpersonaexter':str(idpersonaexter),'pasaporte':str(pasaporte),'numdoc':numdoc,'nombres':nombres,"existe":existe}),content_type="application/json")
                    elif RubroEspecieValorada.objects.filter(serie=request.POST['especie'],rubro__cancelado=False,rubro__fecha__gte=fecha).exists():
                        return HttpResponse(json.dumps({"result":"deuda"}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == "ingresar":
                try:
                    fecha = datetime.now().date() + timedelta(days=-20)
                    if RubroEspecieValorada.objects.filter(id=request.POST['especie'],rubro__cancelado=True,rubro__fecha__gte=fecha).exists():
                        especie =  RubroEspecieValorada.objects.filter(id=request.POST['especie'],rubro__cancelado=True,rubro__fecha__gte=fecha)[:1].get()
                        try:
                            # case server externo
                            client_address = request.META['HTTP_X_FORWARDED_FOR']
                        except:
                            # case localhost o 127.0.0.1
                            client_address = request.META['REMOTE_ADDR']
                        if not PersonaExterna.objects.filter(numdocumento=request.POST['numdoc']).exists() and request.POST['idpersonaexter'] == '0':
                            personaexterna = PersonaExterna(nombres = request.POST['nombres'],
                                                            numdocumento = request.POST['numdoc'],
                                                            pasaporte =  False if request.POST['pasaport']== "False" else True,
                                                            fecha=datetime.now())
                            personaexterna.save()
                        else:
                            if request.POST['idpersonaexter'] == '0':
                                personaexterna = PersonaExterna.objects.filter(numdocumento=request.POST['numdoc'])[:1].get()
                            else:
                                personaexterna = PersonaExterna.objects.filter(id=request.POST['idpersonaexter'])[:1].get()
                            if not PersonaExamenExt.objects.filter(personaextern=personaexterna).exclude(examenexterno=None).exists():
                                personaexterna.nombres = request.POST['nombres']
                                personaexterna.numdocumento = request.POST['numdoc']
                                personaexterna.pasaporte =  False if request.POST['pasaport']== "False" else True
                                personaexterna.fecha=datetime.now()
                                personaexterna.save()

                        if not PersonaExamenExt.objects.filter(especie= especie).exists():
                            personaexamenext = PersonaExamenExt(especie_id = request.POST['especie'],
                                                                personaextern=personaexterna,
                                                                fecha = datetime.now(),
                                                                ipmaquina = client_address)
                        else:
                            personaexamenext = PersonaExamenExt.objects.filter(especie= especie)[:1].get()
                            personaexamenext.ipmaquina = client_address
                        personaexamenext.save()


                        return HttpResponse(json.dumps({"result":"ok",'idexaext':str(personaexamenext.id)}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == "consultacedula":
                try:

                    if PersonaExterna.objects.filter(numdocumento=request.POST['numdoc']).exists():
                        personaexterna = PersonaExterna.objects.filter(numdocumento=request.POST['numdoc'])[:1].get()
                        existe = True if PersonaExamenExt.objects.filter(personaextern=personaexterna).exclude(examenexterno=None).exists() else False
                        return HttpResponse(json.dumps({"result":"ok",'nombres':str(personaexterna.nombres),'existe':existe}),content_type="application/json")
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
            elif action == "addrespuesta":
                try:
                    respuestaexterno = RespuestaExterno.objects.filter(id=request.POST['idresp'])[:1].get()
                    tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(request.POST['hora']),int(request.POST['minut']),int(request.POST['segun']))

                    personaexamenext = PersonaExamenExt.objects.filter(id=request.POST['idpersexaext'],valida=True)[:1].get()
                    personaexamenext.tiempo = tiempo
                    personaexamenext.fechfinaliza = datetime.now()
                    personaexamenext.save()
                    detalleexamenext = DetalleExamenExt.objects.filter(personaexamenext = personaexamenext,respuestaexterno__preguntaexterno = respuestaexterno.preguntaexterno)[:1].get()

                    if request.POST['check'] == 'false':
                        if detalleexamenext.respuestaexterno.valida and personaexamenext.puntaje != 0:
                            personaexamenext.puntaje = personaexamenext.puntaje - detalleexamenext.respuestaexterno.preguntaexterno.puntos
                        detalleexamenext.fecha = None
                    elif detalleexamenext.respuestaexterno.valida and personaexamenext.puntaje != 0 and detalleexamenext.fecha != None:
                        personaexamenext.puntaje = personaexamenext.puntaje - detalleexamenext.respuestaexterno.preguntaexterno.puntos

                    if respuestaexterno.valida and request.POST['check'] == 'true':
                        personaexamenext.puntaje = personaexamenext.puntaje + respuestaexterno.preguntaexterno.puntos

                    if request.POST['check'] == 'true':
                        detalleexamenext.fecha = datetime.now()

                    detalleexamenext.respuestaexterno = respuestaexterno
                    detalleexamenext.save()
                    personaexamenext.save()

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == "actualizatime":
                try:
                    tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(request.POST['hora']),int(request.POST['minut']),int(request.POST['segun']))
                    if PersonaExamenExt.objects.filter(id=request.POST['idpersexaext'],valida=True).exists():
                        personaexamenext = PersonaExamenExt.objects.filter(id=request.POST['idpersexaext'],valida=True)[:1].get()
                        personaexamenext.tiempo = tiempo
                        personaexamenext.fechfinaliza = datetime.now()
                        personaexamenext.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action == "finalizar":
                try:
                    client_address = ip_client_address(request)
                    tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(request.POST['hora']),int(request.POST['minut']),int(request.POST['segun']))
                    if PersonaExamenExt.objects.filter(id=request.POST['idpersexaext'],valida=True).exists():
                        personaexamenext = PersonaExamenExt.objects.filter(id=request.POST['idpersexaext'],valida=True)[:1].get()
                        personaexamenext.tiempo = tiempo
                        personaexamenext.finalizado = True
                        personaexamenext.fechfinaliza = datetime.now()
                        personaexamenext.ipmaquina = client_address
                        if DEFAULT_PASSWORD == 'casade':
                            personaexamenext.valida = False

                        puntaje = DetalleExamenExt.objects.filter(personaexamenext = personaexamenext,respuestaexterno__valida=True).exclude(fecha=None).aggregate(Sum('respuestaexterno__preguntaexterno__puntos'))['respuestaexterno__preguntaexterno__puntos__sum']
                        personaexamenext.puntaje = puntaje
                        personaexamenext.save()

                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except Exception as ex:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        else:
            data={'title':'Examen Externo'}
            addUserData(request,data)
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'examen':
                    try:
                        examenexterno = ExamenExterno.objects.get(id=request.GET['id'])
                        client_address = ip_client_address(request)
                        if DEFAULT_PASSWORD == 'conduccion':
                            if not PersonaExamenExt.objects.filter(id=request.GET['idexaext'],valida=True).exists():
                                return HttpResponseRedirect('/examenexterno?info=Error Vuelva a Ingresar Especie')
                            personaexamenext = PersonaExamenExt.objects.filter(id=request.GET['idexaext'],valida=True)[:1].get()
                            if DetalleExamenExt.objects.filter(personaexamenext=personaexamenext).exists():
                                data['minutos'] = str(personaexamenext.tiempo.time()).split(":")[1]
                                data['horas'] = str(personaexamenext.tiempo.time()).split(":")[0]
                                data['segundos'] = str(personaexamenext.tiempo.time()).split(":")[2]
                                preguntaexamenext = DetalleExamenExt.objects.filter(personaexamenext=personaexamenext).order_by('id')
                            else:
                                tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(str(examenexterno.tiempo.time()).split(":")[0]),int(str(examenexterno.tiempo.time()).split(":")[1]),int('59'))

                                personaexamenext.examenexterno = examenexterno
                                personaexamenext.tiempo = tiempo
                                personaexamenext.comienza = datetime.now()
                                personaexamenext.ipmaquina = client_address
                                personaexamenext.save()
                                for p in PreguntaExterno.objects.filter(examenexterno=examenexterno,activo=True).order_by('?')[:NUMERO_PREGUNTA_EXTERNO]:
                                    respuestaexterno = RespuestaExterno.objects.filter(preguntaexterno=p)[:1].get()
                                    detalleexamenexter = DetalleExamenExt(
                                                    personaexamenext = personaexamenext,
                                                    respuestaexterno = respuestaexterno,
                                                    fecha = None)
                                    detalleexamenexter.save()

                                preguntaexamenext = DetalleExamenExt.objects.filter(personaexamenext=personaexamenext).order_by('id')
                                data['segundos'] = '59'
                                if int(str(examenexterno.tiempo.time()).split(":")[1]) <= 0:
                                    minutos = '59'
                                    if int(int(str(examenexterno.tiempo.time()).split(":")[0])) <= 0:
                                        hora = 0
                                        minutos = 0
                                    else:
                                        hora = int(str(examenexterno.tiempo.time()).split(":")[0]) - 1
                                else:
                                    minutos = int(str(examenexterno.tiempo.time()).split(":")[1])-1
                                    hora = str(examenexterno.tiempo.time()).split(":")[0]
                                data['minutos'] = str(minutos).zfill(2)
                                data['horas'] = str(hora).zfill(2)

                        elif DEFAULT_PASSWORD == 'casade':
                            inscripcion = Inscripcion.objects.filter(persona__usuario=request.user,persona__usuario__is_active=True)[:1].get()
                            if not PersonaExamenExt.objects.filter(inscripcion= inscripcion,examenexterno=examenexterno,valida = True).exists():
                                personaexamenext = PersonaExamenExt(examenexterno=examenexterno,
                                                                    inscripcion=inscripcion,
                                                                    fecha = datetime.now(),
                                                                    comienza = datetime.now(),
                                                                    ipmaquina = client_address)
                            else:
                                personaexamenext = PersonaExamenExt.objects.filter(inscripcion= inscripcion,examenexterno=examenexterno,valida = True)[:1].get()
                                personaexamenext.ipmaquina = client_address
                            personaexamenext.save()
                            if DetalleExamenExt.objects.filter(personaexamenext=personaexamenext).exists():
                                    data['minutos'] = str(personaexamenext.tiempo.time()).split(":")[1]
                                    data['horas'] = str(personaexamenext.tiempo.time()).split(":")[0]
                                    data['segundos'] = str(personaexamenext.tiempo.time()).split(":")[2]
                                    preguntaexamenext = DetalleExamenExt.objects.filter(personaexamenext=personaexamenext).order_by('id')
                            else:
                                tiempo = datetime(datetime.now().year,datetime.now().month,datetime.now().day,int(str(examenexterno.tiempo.time()).split(":")[0]),int(str(examenexterno.tiempo.time()).split(":")[1]),int('59'))

                                personaexamenext.tiempo = tiempo
                                personaexamenext.ipmaquina = client_address
                                personaexamenext.save()
                                for compo in ComponenteExamen.objects.filter(activo=True).order_by('?'):
                                    for p in PreguntaExterno.objects.filter(examenexterno=examenexterno,activo=True,componenteexamen=compo).exclude(respuestaexterno__preguntaexterno=None).order_by('?')[:compo.numpregunt]:
                                        respuestaexterno = RespuestaExterno.objects.filter(preguntaexterno=p)[:1].get()
                                        detalleexamenexter = DetalleExamenExt(
                                                        personaexamenext = personaexamenext,
                                                        respuestaexterno = respuestaexterno,
                                                        fecha = None)
                                        detalleexamenexter.save()

                                preguntaexamenext = DetalleExamenExt.objects.filter(personaexamenext=personaexamenext).order_by('id')
                                data['segundos'] = '59'
                                if int(str(examenexterno.tiempo.time()).split(":")[1]) <= 0:
                                    minutos = '59'
                                    if int(int(str(examenexterno.tiempo.time()).split(":")[0])) <= 0:
                                        hora = 0
                                        minutos = 0
                                    else:
                                        hora = int(str(examenexterno.tiempo.time()).split(":")[0]) - 1
                                else:
                                    minutos = int(str(examenexterno.tiempo.time()).split(":")[1])-1
                                    hora = str(examenexterno.tiempo.time()).split(":")[0]
                                data['minutos'] = str(minutos).zfill(2)
                                data['horas'] = str(hora).zfill(2)
                        else:
                            return HttpResponseRedirect('/examenexterno?info=no puede ingresar al modulo')

                        data['examenexterno'] = examenexterno

                        paging = MiPaginador(preguntaexamenext, NUMERO_PREGUNTA_EXTERNO)
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
                        data['preguntaexamenext'] = page.object_list
                        data['personaexamenext'] = personaexamenext
                        data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD

                        return render(request ,"examenexterno/examen.html" ,  data)
                    except Exception as e:
                        return HttpResponseRedirect('/?info='+str(e))
                elif action == "resultado":
                    try:
                        examenexterno = ExamenExterno.objects.get(id=request.GET['id'])

                        if PersonaExamenExt.objects.filter(id=request.GET['idexaext']).exists():
                            personaexamenext = PersonaExamenExt.objects.filter(id=request.GET['idexaext'])[:1].get()
                            preguntaexamenext = DetalleExamenExt.objects.filter(personaexamenext=personaexamenext).order_by('id')



                            data['examenexterno'] = examenexterno

                            paging = MiPaginador(preguntaexamenext, NUMERO_PREGUNTA_EXTERNO)
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
                            data['preguntaexamenext'] = page.object_list
                            data['personaexamenext'] = personaexamenext
                            data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                            data['NOTA_PARA_EXAMEN_EXTERNO'] = NOTA_PARA_EXAMEN_EXTERNO

                            return render(request ,"examenexterno/resultado.html" ,  data)
                        return HttpResponseRedirect('/examenexterno?info=Error Vuelva a Ingresar Especie')
                    except Exception as e:
                        return HttpResponseRedirect('/examenexterno?idexaext='+str(request.GET['idexaext']))


            else:
                if 'info' in request.GET:
                    data['info'] = request.GET['info']
                data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD

                client_address = ip_client_address(request)
                ips_aulas = [x.ip for x in Aula.objects.filter(activa=False,tipo__id=TIPO_AULA)]
                if DEFAULT_PASSWORD != 'casade':
                    if not client_address in ips_aulas or not EXAMEN_EXTERNO_INGRESO:
                        return HttpResponseRedirect('/?info=No puede ingresar al modulo desde este equipo')

                if 'idexaext' in request.GET:

                    if PersonaExamenExt.objects.filter(id=request.GET['idexaext'],examenexterno=None).exists():
                        data['idexaext'] = request.GET['idexaext']
                        data['inciarexamen'] = False
                    else:
                        if PersonaExamenExt.objects.filter(id=request.GET['idexaext'],finalizado = True):
                            return HttpResponseRedirect('/examenexterno?info=EL examen se encuentra finalizado')
                        data['inciarexamen'] = True
                    personaexamenext = PersonaExamenExt.objects.filter(id=request.GET['idexaext'])[:1].get()
                    data['idexaext'] = personaexamenext.id
                    idexamen = PersonaExamenExt.objects.filter(personaextern=personaexamenext.personaextern,valida=True).exclude(examenexterno=None).values('examenexterno')
                    data['examenexterno'] = ExamenExterno.objects.filter(activo=True).exclude(id__in=idexamen)
                    data['personaextern'] = personaexamenext.personaextern
                elif DEFAULT_PASSWORD == 'casade':
                    if not Inscripcion.objects.filter(persona__usuario=request.user,persona__usuario__is_active=True).exists():
                        return HttpResponseRedirect('/?info=No se encuentra inscrito, no puede ingresar al modulo')
                    inscripcion = Inscripcion.objects.filter(persona__usuario=request.user,persona__usuario__is_active=True)[:1].get()
                    if inscripcion.tiene_deuda():
                        return HttpResponseRedirect('/?info=tiene deuda, no puede ingresar al modulo')
                    if not inscripcion.grupo().id in ID_GRUPO_EXAMEN_CASADE:
                        return HttpResponseRedirect('/?info=No se encuentra inscrito, no puede ingresar al modulo')
                    idexamen = PersonaExamenExt.objects.filter(inscripcion=inscripcion,valida=True,finalizado=True).exclude(examenexterno=None).values('examenexterno')
                    data['examenexterno'] = ExamenExterno.objects.filter(activo=True).exclude(id__in=idexamen)
                    data['idexaext'] = True
                data['DEFAULT_PASSWORD'] = DEFAULT_PASSWORD
                return render(request ,"examenexterno/menu.html" ,  data)
    except Exception as ex:
        return HttpResponseRedirect('/?info='+str(ex))
