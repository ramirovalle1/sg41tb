from datetime import datetime
from django.contrib.auth.decorators import login_required
import json
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render

from settings import CARRERAS_ID_EXCLUIDAS_INEC
from sga.commonviews import addUserData
from sga.models import Periodo, EncuestaItb, Inscripcion, Coordinacion, Carrera, NucleoFamiliar, Persona, Matricula, \
    ZonaResidencia, CondicionesHogar, Genero, MaterialCasa, TipoEmpleo, TipoIngresoHogar, TipoIngresoPropio, \
    UsoTransporte, TipoTransporte, Deporte, ManifestacionArtistica, TipoServicio, Afiliacion

from django.core.paginator import Paginator
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
        nucleos = NucleoFamiliar.objects.all().order_by('nombre')
        zona = ZonaResidencia.objects.all().order_by('nombre')
        condiciones = CondicionesHogar.objects.all().order_by('nombre')
        genero = Genero.objects.filter().order_by('id')
        materialcasa = MaterialCasa.objects.filter().order_by('nombre')
        ingresoh = TipoIngresoHogar.objects.filter().order_by('nombre')
        ingresop =TipoIngresoPropio.objects.filter().order_by('nombre')
        empleo = TipoEmpleo.objects.filter().order_by('nombre')
        usotransporte = UsoTransporte.objects.filter().order_by('nombre')
        tipotransporte = TipoTransporte.objects.filter().order_by('nombre')
        deportes = Deporte.objects.filter().order_by('nombre')
        manifestaciones = ManifestacionArtistica.objects.filter().order_by('nombre')
        servicios = TipoServicio.objects.filter().order_by('nombre')
        afiliacion = Afiliacion.objects.filter().order_by('nombre')
        if request.method == 'POST':
            action = request.POST['action']
            encuestas =EncuestaItb.objects.filter().values('inscripcion')
            inscripcion = Inscripcion.objects.filter(id__in=encuestas).distinct()
            # carreras = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # ,activo=True, carrera=True

            if action =='buscarnucleoxcarrera':
                try:
                    data={'title':''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio'])>0:
                        encuesta = encuestas.filter(fecharealizado__year= anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcarrera']) > 0:
                        carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                        inscripcion = inscripcion.filter(carrera=carrera)

                    listacarrera = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre') #, activo=True,carrera=True

                    lista= [{"carreranombre": str(c.nombre),
                                                  "info": [{
                                                      "nombre": n.nombre,
                                                      "cantidad":  EncuestaItb.objects.filter(nucleofamiliar =n, carrera=c, inscripcion__in= inscripcion).count()
                                                  } for n in nucleos]
                                            } for c in listacarrera]

                    if lista:
                        data['listcarreraxn']= lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")

            elif action=='buscarnucleoxcoordinacion':
                try:
                    data={"title":''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcoordinacion'])>0:
                        coordinacion = Coordinacion.objects.get(id = int(request.POST['idcoordinacion']))
                        inscripcion = inscripcion.filter(carrera__in= coordinacion.carrera.all())
                    listacoordinacion =Coordinacion.objects.filter(carrera__in=inscripcion.values('carrera')).distinct()

                    lista=[{"coordnombre":str(lc.nombre),
                                                  "info":[{ "nombre":nc.nombre,
                                                            "cantidad": EncuestaItb.objects.filter(nucleofamiliar =nc,carrera__in=lc.carrera.all(), inscripcion__in= inscripcion).count()
                                                          }for nc in nucleos]
                                                  }for lc in listacoordinacion]
                    if lista:
                        data['listcoordinacionxn'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")

            elif action =='buscarzonaxcarrera':
                try:
                    data = {'title': ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcarrera']) > 0:
                        carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                        inscripcion = inscripcion.filter(carrera=carrera)

                    listacarrera = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # , activo=True,carrera=True

                    lista= [{"carreranombre": str(c.nombre),
                                                    "info": [{"nombre": zn.nombre,
                                                              "cantidad": EncuestaItb.objects.filter(zona=zn, carrera=c,  inscripcion__in= inscripcion).count()
                                                             } for zn in zona]
                                                    } for c in listacarrera]

                    if lista:
                        data['listcarreraxzonares'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(ex)}),content_type="application/json")

            elif action == 'buscarzonaxcoordinacion':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcoordinacion']) > 0:
                        coordinacion = Coordinacion.objects.get(id=int(request.POST['idcoordinacion']))
                        inscripcion = inscripcion.filter(carrera__in=coordinacion.carrera.all())
                    listacoordinacion = Coordinacion.objects.filter(carrera__in=inscripcion.values('carrera__id')).distinct()
                    lista = [{"coordnombre": str(lc.nombre),
                                                   "info": [{"nombre": zn.nombre,
                                                             "cantidad": EncuestaItb.objects.filter(zona=zn, carrera__in=lc.carrera.all(),  inscripcion__in= inscripcion).count()
                                                             } for zn in zona]
                                                   } for lc in listacoordinacion]

                    if lista:
                        data['listcoordinacionxzonares'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),
                                        content_type="application/json")

            elif action == 'buscarcondhogarxcarrera':
                try:
                    data = {'title': ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcarrera']) > 0:
                        carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                        inscripcion = inscripcion.filter(carrera=carrera)
                    listacarrera = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # , activo=True,carrera=True
                    lista = [{"carreranombre": str(c.nombre),
                                                    "info": [{"nombre": cn.nombre,
                                                              "cantidad": EncuestaItb.objects.filter(condicion=cn,carrera=c, inscripcion__in = inscripcion).count()
                                                              } for cn in condiciones]
                                                    } for c in listacarrera]

                    if lista:
                        data['listcarreraxcond'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(ex)}),content_type="application/json")

            elif action == 'buscarcondhogarxcoordinacion':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)
                    if int(request.POST['idcoordinacion']) > 0:
                        coordinacion = Coordinacion.objects.get(id=int(request.POST['idcoordinacion']))
                        inscripcion = inscripcion.filter(carrera__in=coordinacion.carrera.all())
                    listacoordinacion = Coordinacion.objects.filter(carrera__in=inscripcion.values('carrera__id')).distinct()
                    lista = [{"coordnombre": str(lc.nombre),
                                                           "info": [{"nombre": cond.nombre,
                                                                     "cantidad": EncuestaItb.objects.filter(condicion= cond, carrera__in=lc.carrera.all(), inscripcion__in = inscripcion).count()
                                                                    } for cond in condiciones]
                                                   } for lc in listacoordinacion]
                    if lista:
                        data['listcoordinacionxcondhogar'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")

            elif action =='buscargenerosxcarrera':
                try:
                    data = {'title': ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcarrera']) > 0:
                        carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                        inscripcion = inscripcion.filter(carrera=carrera)
                    listacarrera = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # , activo=True,carrera=True
                    lista = [{"carreranombre": str(c.nombre),
                                                    "info": [{"nombre": g.nombre,
                                                              "cantidad": EncuestaItb.objects.filter(genero=g,carrera=c, inscripcion__in= inscripcion).count()
                                                              } for g in genero]
                                                    } for c in listacarrera]
                    if lista:
                        data['listcarreraxgener']= lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")

            elif action == 'buscargenerosxcoordinacion':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcoordinacion']) > 0:
                        coordinacion = Coordinacion.objects.get(id=int(request.POST['idcoordinacion']))
                        inscripcion = inscripcion.filter(carrera__in=coordinacion.carrera.all())
                    listacoordinacion = Coordinacion.objects.filter(carrera__in=inscripcion.values('carrera')).distinct()
                    lista = [{"coordnombre": str(lc.nombre),
                                                           "info": [{"nombre": g.nombre,
                                                                     "cantidad": EncuestaItb.objects.filter(genero= g, carrera__in=lc.carrera.all(), inscripcion__in = inscripcion).count()
                                                                    } for g in genero]
                                                   } for lc in listacoordinacion]
                    if lista:
                        data['listcoordinacionxgener'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}),content_type="application/json")

            elif action =='buscarmaterialxcarrera':
                try:
                    data ={"title":''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcarrera']) > 0:
                        carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                        inscripcion = inscripcion.filter(carrera=carrera)
                    listacarrera = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # , activo=True,carrera=True
                    lista = [{"carreranombre": str(c.nombre),
                                                    "info": [{"nombre": m.nombre,
                                                              "cantidad": EncuestaItb.objects.filter(materialcasa=m,carrera=c).count()
                                                              } for m in materialcasa]
                                                    } for c in listacarrera]
                    if lista:
                        data['listcarreraxmat'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)},content_type="application/json"))

            elif action =='buscarmaterialxcoordinacion':
                try:
                    data={"title":''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcoordinacion']) > 0:
                        coordinacion = Coordinacion.objects.get(id=int(request.POST['idcoordinacion']))
                        inscripcion = inscripcion.filter(carrera__in=coordinacion.carrera.all())
                    listacoordinacion = Coordinacion.objects.filter(carrera__in=inscripcion.values('carrera')).distinct()
                    lista = [{"coordnombre": str(lc.nombre),
                                                           "info": [{"nombre": mc.nombre,
                                                                     "cantidad": EncuestaItb.objects.filter(materialcasa= mc, carrera__in=lc.carrera.all(), inscripcion__in =inscripcion).count()
                                                                    } for mc in materialcasa]
                                                   } for lc in listacoordinacion]
                    if lista:
                        data['listcoordinacionxmat'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)},content_type="application/json"))

            elif action =='buscarservicioxcarrera':
                try:
                    data ={"title":''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcarrera']) > 0:
                        carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                        inscripcion = inscripcion.filter(carrera=carrera)
                    listacarrera = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # , activo=True,carrera=True
                    lista = [{"carreranombre": str(c.nombre),
                              "info": [{"nombre": s.nombre,
                                      "cantidad": EncuestaItb.objects.filter(servicio=s,carrera=c, inscripcion__in=inscripcion).count()
                                      } for s in servicios]
                             } for c in listacarrera]
                    if lista:
                        data['listcarreraxserv'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)},content_type="application/json"))

            elif action =='buscarservicioxcoordinacion':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcoordinacion']) > 0:
                        coordinacion = Coordinacion.objects.get(id=int(request.POST['idcoordinacion']))
                        inscripcion = inscripcion.filter(carrera__in=coordinacion.carrera.all())
                    listacoordinacion = Coordinacion.objects.filter(carrera__in=inscripcion.values('carrera')).distinct()
                    lista = [{"coordnombre": str(lc.nombre),
                              "info": [{"nombre": s.nombre,
                                        "cantidad": EncuestaItb.objects.filter(servicio=s, carrera__in=lc.carrera.all(),inscripcion__in=inscripcion).count()
                                        } for s in servicios]
                              } for lc in listacoordinacion]
                    if lista:
                        data['listcoordinacionxserv'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(
                        json.dumps({'result': 'bad', 'message': str(e)}, content_type="application/json"))

            elif action =='buscarafiliacionxcarrera':
                try:
                    data ={"title":''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcarrera']) > 0:
                        carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                        inscripcion = inscripcion.filter(carrera=carrera)
                    listacarrera = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # , activo=True,carrera=True
                    lista = [{"carreranombre": str(c.nombre),
                              "info": [{"nombre": a.nombre,
                                      "cantidad": EncuestaItb.objects.filter(afiliacion=a,carrera=c, inscripcion__in=inscripcion).count()
                                      } for a in afiliacion]
                             } for c in listacarrera]
                    if lista:
                        data['listcarreraxafilacion'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)},content_type="application/json"))

            elif action == 'buscarafiliacionxcoordinacion':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcoordinacion']) > 0:
                        coordinacion = Coordinacion.objects.get(id=int(request.POST['idcoordinacion']))
                        inscripcion = inscripcion.filter(carrera__in=coordinacion.carrera.all())
                    listacoordinacion = Coordinacion.objects.filter(carrera__in=inscripcion.values('carrera')).distinct()
                    lista = [{"coordnombre": str(lc.nombre),
                              "info": [{"nombre": a.nombre,
                                        "cantidad": EncuestaItb.objects.filter(afiliacion=a, carrera__in=lc.carrera.all(),inscripcion__in=inscripcion).count()
                                        } for a in afiliacion]
                              } for lc in listacoordinacion]
                    if lista:
                        data['listcoordinacionxafiliacion'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(
                        json.dumps({'result': 'bad', 'message': str(e)}, content_type="application/json"))

            elif action =='buscaringresohxcarrera':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)
                    if int(request.POST['idcarrera']) > 0:
                        carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                        inscripcion = inscripcion.filter(carrera=carrera)
                    listacarrera = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # , activo=True,carrera=True
                    lista = [{"carreranombre": str(c.nombre),
                              "info": [{"nombre": ingh.nombre,
                                        "cantidad": EncuestaItb.objects.filter(ingresohogar=ingh, carrera=c, inscripcion__in=inscripcion).count()
                                        } for ingh in ingresoh]
                              } for c in listacarrera]
                    if lista:
                        data['listcarreraxih'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message':str(e)}),content_type="application/json")

            elif action=='buscaringresohxcoordinacion':
                try:
                    data={"title":''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcoordinacion']) > 0:
                        coordinacion = Coordinacion.objects.get(id=int(request.POST['idcoordinacion']))
                        inscripcion = inscripcion.filter(carrera__in=coordinacion.carrera.all())
                    listacoordinacion = Coordinacion.objects.filter(carrera__in=inscripcion.values('carrera')).distinct()
                    lista = [{"coordnombre": str(lc.nombre),
                              "info": [{"nombre": ingh.nombre,
                                        "cantidad": EncuestaItb.objects.filter(ingresohogar=ingh,carrera__in=lc.carrera.all(),inscripcion__in=inscripcion).count()
                                        } for ingh in ingresoh]
                              } for lc in listacoordinacion]
                    if lista:
                        data['listcoordinacionxingh'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result':'bad', 'message':str(e)}),content_type="application/json")

            elif action =='buscaringresopxcarrera':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)
                    if int(request.POST['idcarrera']) > 0:
                        carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                        inscripcion = inscripcion.filter(carrera=carrera)
                    listacarrera = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # , activo=True,carrera=True
                    lista = [{"carreranombre": str(c.nombre),
                              "info": [{"nombre": ingp.nombre,
                                        "cantidad": EncuestaItb.objects.filter(ingresopropio=ingp, carrera=c, inscripcion__in=inscripcion).count()
                                        } for ingp in ingresop]
                              } for c in listacarrera]
                    if lista:
                        data['listcarreraxip'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result': 'bad', 'message':str(e)}),content_type="application/json")

            elif action=='buscaringresopxcoordinacion':
                try:
                    data={"title":''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcoordinacion']) > 0:
                        coordinacion = Coordinacion.objects.get(id=int(request.POST['idcoordinacion']))
                        inscripcion = inscripcion.filter(carrera__in=coordinacion.carrera.all())
                    listacoordinacion = Coordinacion.objects.filter(carrera__in=inscripcion.values('carrera')).distinct()
                    lista = [{"coordnombre": str(lc.nombre),
                              "info": [{"nombre": ingp.nombre,
                                        "cantidad": EncuestaItb.objects.filter(ingresopropio=ingp,carrera__in=lc.carrera.all(),inscripcion__in=inscripcion).count()
                                        } for ingp in ingresop]
                              } for lc in listacoordinacion]
                    if lista:
                        data['listcoordinacionxingp'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as e:
                    return HttpResponse(json.dumps({'result':'bad', 'message':str(e)}),content_type="application/json")

            elif action=='buscarxcarreraemp':
                try:
                    data={"title":''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) >0 :
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcarrera']) > 0:
                        carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                        inscripcion = inscripcion.filter(carrera=carrera)
                    listacarrera = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # , activo=True,carrera=True
                    lista = [{"carreranombre": str(c.nombre),
                              "info": [{"nombre": emp.nombre,
                                        "cantidad": EncuestaItb.objects.filter(empleo=emp, carrera=c,inscripcion__in=inscripcion).count()
                                        } for emp in empleo]
                              } for c in listacarrera]
                    if lista:
                        data['listcarreraxemp'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','message':str(ex)}),content_type="application/json")

            elif action=='buscarxcoordinacionemp':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcoordinacion']) > 0:
                        coordinacion = Coordinacion.objects.get(id=int(request.POST['idcoordinacion']))
                        inscripcion = inscripcion.filter(carrera__in=coordinacion.carrera.all())
                    listacoordinacion = Coordinacion.objects.filter(carrera__in=inscripcion.values('carrera')).distinct()
                    lista = [{"coordnombre": str(lc.nombre),
                              "info": [{"nombre": emp.nombre,
                                        "cantidad": EncuestaItb.objects.filter(empleo=emp,carrera__in=lc.carrera.all(),inscripcion__in=inscripcion).count()
                                        } for emp in empleo]
                              } for lc in listacoordinacion]
                    if lista:
                        data['listcoordinacionxemp'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','message':str(ex)}),content_type="application/json")

            elif action=='buscarutrasportexcarrera':
                try:
                    data={"title":''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) >0 :
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcarrera']) > 0:
                        carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                        inscripcion = inscripcion.filter(carrera=carrera)
                    listacarrera = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # , activo=True,carrera=True
                    lista = [{"carreranombre": str(c.nombre),
                              "info": [{"nombre": ut.nombre,
                                        "cantidad": EncuestaItb.objects.filter(usotransporte=ut, carrera=c,inscripcion__in=inscripcion).count()
                                        } for ut in usotransporte]
                              } for c in listacarrera]
                    if lista:
                        data['listcarrxutrasporte'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','message':str(ex)}),content_type="application/json")

            elif action =='buscarutrasportexcoordinacion':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcoordinacion']) > 0:
                        coordinacion = Coordinacion.objects.get(id=int(request.POST['idcoordinacion']))
                        inscripcion = inscripcion.filter(carrera__in=coordinacion.carrera.all())
                    listacoordinacion = Coordinacion.objects.filter(
                        carrera__in=inscripcion.values('carrera')).distinct()
                    lista = [{"coordnombre": str(lc.nombre),
                              "info": [{"nombre": ut.nombre,
                                        "cantidad": EncuestaItb.objects.filter(usotransporte=ut, carrera__in=lc.carrera.all(),inscripcion__in=inscripcion).count()
                                        } for ut in usotransporte]
                              } for lc in listacoordinacion]
                    if lista:
                        data['listcoordinacionxutrasporte'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad', 'message':str(ex)}),content_type="application/json")

            elif action =='buscartransportetxcarrera':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcarrera']) > 0:
                        carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                        inscripcion = inscripcion.filter(carrera=carrera)
                    listacarrera = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # , activo=True,carrera=True
                    lista = [{"carreranombre": str(c.nombre),
                              "info": [{"nombre": t.nombre,
                                        "cantidad": EncuestaItb.objects.filter(transporte=t, carrera=c,inscripcion__in=inscripcion).count()
                                        } for t in tipotransporte]
                              } for c in listacarrera]
                    if lista:
                        data['listcarrxttransporte'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','message':str(ex)}),content_type="application/json")

            elif action =='buscarxcoordinaciontranst':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcoordinacion']) > 0:
                        coordinacion = Coordinacion.objects.get(id=int(request.POST['idcoordinacion']))
                        inscripcion = inscripcion.filter(carrera__in=coordinacion.carrera.all())
                    listacoordinacion = Coordinacion.objects.filter(carrera__in=inscripcion.values('carrera')).distinct()

                    lista = [{"coordnombre": str(lc.nombre),
                              "info": [{"nombre": t.nombre,
                                        "cantidad": EncuestaItb.objects.filter(transporte=t,carrera__in=lc.carrera.all(),inscripcion__in=inscripcion).count()
                                        } for t in tipotransporte]
                              } for lc in listacoordinacion]
                    if lista:
                        data['listcoordinacionxtransportet'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','message':str(ex)}),content_type="application/json")

            elif action =='buscardeportexcarrera':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcarrera']) > 0:
                        carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                        inscripcion = inscripcion.filter(carrera=carrera)
                    listacarrera = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # , activo=True,carrera=True
                    lista = [{"carreranombre": str(c.nombre),
                              "info": [{"nombre": dep.nombre,
                                        "cantidad": EncuestaItb.objects.filter(deporte__contains=str(dep.pk),carrera=c,inscripcion__in=inscripcion).count()
                                        } for dep in deportes]
                              } for c in listacarrera]
                    if lista:
                        data['listcarrxdeporte'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")

                except Exception as ex:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(ex)}),content_type="application/json")

            elif action =='buscardeportexcoordinacion':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcoordinacion']) > 0:
                        coordinacion = Coordinacion.objects.get(id=int(request.POST['idcoordinacion']))
                        inscripcion = inscripcion.filter(carrera__in=coordinacion.carrera.all())
                    listacoordinacion = Coordinacion.objects.filter(carrera__in=inscripcion.values('carrera')).distinct()

                    lista = [{"coordnombre": str(lc.nombre),
                              "info": [{"nombre": dep.nombre,
                                        "cantidad": EncuestaItb.objects.filter(deporte__contains=str(dep.pk),carrera__in=lc.carrera.all(),inscripcion__in=inscripcion).count()
                                        } for dep in deportes]
                              } for lc in listacoordinacion]
                    if lista:
                        data['listcoordinacionxdeporte'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result':'bad','message':str(ex)}),content_type="application/json")

            elif action =='buscarmanifestacionxcarrera':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcarrera']) > 0:
                        carrera = Carrera.objects.get(pk=int(request.POST['idcarrera']))
                        inscripcion = inscripcion.filter(carrera=carrera)
                    listacarrera = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # , activo=True,carrera=True
                    lista = [{"carreranombre": str(c.nombre),
                              "info": [{"nombre": man.nombre,
                                        "cantidad": EncuestaItb.objects.filter(manifestacion=man, carrera=c,inscripcion__in=inscripcion).count()
                                        } for man in manifestaciones]
                              } for c in listacarrera]
                    if lista:
                        data['listcarrxmanifestacion'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(ex)}),content_type="application/json")

            elif action =='buscarxcoordinacionmanifestacion':
                try:
                    data = {"title": ''}
                    anio = request.POST['idanio']
                    if int(request.POST['idanio']) > 0:
                        encuesta = encuestas.filter(fecharealizado__year=anio)
                        inscripcion = inscripcion.filter(id__in=encuesta)

                    if int(request.POST['idcoordinacion']) > 0:
                        coordinacion = Coordinacion.objects.get(id=int(request.POST['idcoordinacion']))
                        inscripcion = inscripcion.filter(carrera__in=coordinacion.carrera.all())
                    listacoordinacion = Coordinacion.objects.filter(carrera__in=inscripcion.values('carrera')).distinct()

                    lista = [{"coordnombre": str(lc.nombre),
                              "info": [{"nombre": man.nombre,
                                        "cantidad": EncuestaItb.objects.filter(manifestacion=man, carrera__in=lc.carrera.all(),inscripcion__in=inscripcion).count()
                                        } for man in manifestaciones]
                              } for lc in listacoordinacion]
                    if lista:
                        data['listcoordinacionxmanifestacion'] = lista
                        data['result'] = 'ok'
                        return HttpResponse(json.dumps(data), content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({'result': 'bad'}), content_type="application/json")
                except Exception as ex:
                    return HttpResponse(json.dumps({'result': 'bad', 'message': str(ex)}),content_type="application/json")
        else:
            data = {'title': 'Encuesta de Ingreso ITB'}
            addUserData(request, data)
            inscripcion = Inscripcion.objects.filter( id__in=EncuestaItb.objects.filter().values('inscripcion')).distinct()
            carreras = Carrera.objects.filter(id__in=inscripcion.values('carrera__id')).order_by('nombre')  # ,activo=True, carrera=True

            if 'action' in request.GET:
                action = request.GET['action']
                # ACCIONES PARA TABLAS Y GRAFICAS
                if action == 'graph_nucleofamiliar':
                    try:
                        data = {'title': 'Tipos de nucleo familiar de los estudiantes'}
                        addUserData(request, data)
                        aniosencuestas = EncuestaItb.objects.filter().values_list('fecharealizado__year',flat=True).distinct()
                        data['listanio'] = [{"anio": i} for i in aniosencuestas]
                        coordinaciones = Coordinacion.objects.filter(carrera__in=carreras).distinct()
                        #CARRERA
                        data['lista_carreras_nucleofam'] = [{"carreranombre": str(c.nombre),
                                                                  "data": [{
                                                                      "nombre": n.nombre,
                                                                      "cantidad":  EncuestaItb.objects.filter(nucleofamiliar =n, carrera=c).count()
                                                                  } for n in nucleos]
                                                            } for c in carreras]

                        data['lista_coordinaciones_nucleofam'] = [{"coordnombre": str(c.nombre),
                                                                   "data": [{
                                                                            "nombre": n.nombre,
                                                                            "cantidad": EncuestaItb.objects.filter(nucleofamiliar =n, carrera__in=c.carrera.all()).count()
                                                                            } for n in nucleos]
                                                                  } for c in coordinaciones]

                        data['lista_nucleo_resumen'] = [{"nucleonombre": str(c.nombre),
                                                                 "cantidad":  EncuestaItb.objects.filter(nucleofamiliar=c).count()
                                                        }for c in nucleos]
                        data['listadocarreras'] = carreras
                        data['listcoordinaciones'] = coordinaciones
                        data['nucleosfamiliares'] = nucleos
                        return render(request, "cons_encuestaingreso/graf_nucleofamiliar.html", data)
                    except Exception as ex:
                        print(ex)

                elif action=='graph_zonaresidencia':
                    try:
                        data = {'title': 'Zona de Residencia de los estudiantes'}
                        addUserData(request, data)
                        aniosencuestas = EncuestaItb.objects.filter().values_list('fecharealizado__year',flat=True).distinct()
                        data['listanio'] = [{"anio": i} for i in aniosencuestas]
                        coordinaciones = Coordinacion.objects.filter(carrera__in=carreras).distinct()
                        # CARRERA
                        data['lista_carreras_zonares'] = [{"carreranombre": str(c.nombre),
                                                           "data": [{
                                                                 "nombre": zn.nombre,
                                                                 "cantidad": EncuestaItb.objects.filter(zona=zn, carrera=c).count()
                                                           } for zn in zona]
                                                         } for c in carreras]

                        data['lista_coordinaciones_zonares'] = [{"coordnombre": str(c.nombre),
                                                                  "data": [{
                                                                            "nombre": zn.nombre,
                                                                            "cantidad": EncuestaItb.objects.filter(zona=zn,carrera__in=c.carrera.all()).count()
                                                                         } for zn in zona]
                                                                } for c in coordinaciones]

                        data['lista_zona_resumen'] = [{"zonanombre": str(zn.nombre),
                                                         "cantidad": EncuestaItb.objects.filter(zona=zn).count()
                                                      }for zn in zona]

                        data['listadocarreras'] = carreras
                        data['listcoordinaciones'] = coordinaciones
                        data['zonasres'] = zona
                        return render(request, "cons_encuestaingreso/graf_zonaresidencia.html", data)
                    except Exception as ex:
                        print(ex)

                elif action =="graph_condicioneshogar":
                    try:
                        data = {'title': 'Condiciones de Hogar de los estudiantes'}
                        addUserData(request, data)
                        aniosencuestas = EncuestaItb.objects.filter().values_list('fecharealizado__year',flat=True).distinct()
                        data['listanio'] = [{"anio": i} for i in aniosencuestas]
                        coordinaciones = Coordinacion.objects.filter(carrera__in=carreras).distinct()
                        # CARRERA
                        data['lista_carreras_codhogar'] = [{"carreranombre": str(c.nombre),
                                                           "data": [{ "nombre": cond.nombre,
                                                                      "cantidad": EncuestaItb.objects.filter(condicion=cond,carrera=c).count()
                                                                    } for cond in condiciones]
                                                           } for c in carreras]

                        data['lista_coordinaciones_codhogar'] = [{"coordnombre": str(c.nombre),
                                                                 "data": [{"nombre": cond.nombre,
                                                                           "cantidad": EncuestaItb.objects.filter(condicion=cond,carrera__in=c.carrera.all()).count()
                                                                          } for cond in condiciones]
                                                                 } for c in coordinaciones]

                        data['lista_condiciones_resumen'] = [{"condnombre": str(cond.nombre),
                                                                "cantidad": EncuestaItb.objects.filter(condicion=cond).count()
                                                             } for cond in condiciones]

                        data['listadocarreras'] = carreras
                        data['listcoordinaciones'] = coordinaciones
                        data['condhogares'] = condiciones
                        return render(request, "cons_encuestaingreso/graf_condicioneshogar.html", data)
                    except Exception as ex:
                        print(ex)

                elif action=="graph_genero":
                    try:
                        data = {'title': 'Generos de los estudiantes'}
                        addUserData(request, data)
                        aniosencuestas = EncuestaItb.objects.filter().values_list('fecharealizado__year',flat=True).distinct()
                        data['listanio'] = [{"anio": i} for i in aniosencuestas]
                        coordinaciones = Coordinacion.objects.filter(carrera__in=carreras).distinct()
                        # CARRERA
                        data['lista_carreras_genero'] = [{"carreranombre": str(c.nombre),
                                                            "data": [{"nombre": g.nombre,
                                                                      "cantidad": EncuestaItb.objects.filter(genero=g, carrera=c).count()
                                                                      } for g in genero]
                                                            } for c in carreras]

                        data['lista_coordinaciones_genero'] = [{"coordnombre": str(c.nombre),
                                                                  "data": [{"nombre": g.nombre,
                                                                            "cantidad": EncuestaItb.objects.filter(genero=g,carrera__in=c.carrera.all()).count()
                                                                            } for g in genero]
                                                                  } for c in coordinaciones]

                        data['lista_genero_resumen'] = [{"gennombre": str(g.nombre),
                                                         "cantidad": EncuestaItb.objects.filter(genero=g).count()
                                                         } for g in genero]

                        data['listadocarreras'] = carreras
                        data['listcoordinaciones'] = coordinaciones
                        data['listgeneros'] = genero
                        return render(request, "cons_encuestaingreso/graf_genero.html", data)
                    except Exception as ex:
                        print(ex)

                elif action =="graph_materiales":
                    try:
                        data = {'title': 'Materiales predominantes de Viviendas'}
                        addUserData(request, data)
                        coordinaciones = Coordinacion.objects.filter(carrera__in=carreras).distinct()
                        aniosencuestas = EncuestaItb.objects.filter().values_list('fecharealizado__year',flat=True).distinct()
                        data['listanio'] = [{"anio": i} for i in aniosencuestas]
                        # CARRERA
                        data['lista_carreras_materiales'] = [{"carreranombre": str(c.nombre),
                                                          "data": [{"nombre": mc.nombre,
                                                                    "cantidad": EncuestaItb.objects.filter(materialcasa=mc,carrera=c).count()
                                                                    } for mc in materialcasa]
                                                          } for c in carreras]

                        data['lista_coordinaciones_materiales'] = [{"coordnombre": str(c.nombre),
                                                                "data": [{"nombre": mc.nombre,
                                                                          "cantidad": EncuestaItb.objects.filter(materialcasa=mc,carrera__in=c.carrera.all()).count()
                                                                          } for mc in materialcasa]
                                                                } for c in coordinaciones]

                        data['lista_material_resumen'] = [{"gennombre": str(mc.nombre),
                                                         "cantidad": EncuestaItb.objects.filter(materialcasa=mc).count()
                                                         } for mc in materialcasa]

                        data['lista_carreras_servicio'] =[{"carreranombre": str(c.nombre),
                                                           "data": [{"nombre": s.nombre,
                                                                    "cantidad": EncuestaItb.objects.filter(servicio=s,carrera=c).count()
                                                                    } for s in servicios]
                                                          } for c in carreras]
                        data['lista_coordinaciones_servicios']=[{"coordnombre": str(c.nombre),
                                                                "data": [{"nombre": s.nombre,
                                                                          "cantidad": EncuestaItb.objects.filter(servicio=s,carrera__in=c.carrera.all()).count()
                                                                          } for s in servicios]
                                                                } for c in coordinaciones]

                        data['lista_servicios_resumen'] = [{"servnombre": str(s.nombre),
                                                           "cantidad": EncuestaItb.objects.filter(servicio=s).count()
                                                           } for s in servicios]

                        data['lista_carreras_afiliacion'] = [{"carreranombre": str(c.nombre),
                                                            "data": [{"nombre": a.nombre,
                                                                      "cantidad": EncuestaItb.objects.filter(afiliacion=a,carrera=c).count()
                                                                      } for a in afiliacion]
                                                            } for c in carreras]
                        data['lista_coordinaciones_afiliacion'] = [{"coordnombre": str(c.nombre),
                                                                   "data": [{"nombre": a.nombre,
                                                                             "cantidad": EncuestaItb.objects.filter(afiliacion=a,carrera__in=c.carrera.all()).count()
                                                                             } for a in afiliacion]
                                                                   } for c in coordinaciones]

                        data['lista_afiliacion_resumen'] = [{"afiliacion_nombre": str(a.nombre),
                                                            "cantidad": EncuestaItb.objects.filter(afiliacion=a).count()
                                                            } for a in afiliacion]
                        data['listadocarreras'] = carreras
                        data['listcoordinaciones'] = coordinaciones
                        data['listmaterial'] = materialcasa
                        data['listservicio'] = servicios
                        data['listafiliacion'] = afiliacion

                        return render(request,"cons_encuestaingreso/graf_materiales.html",data)
                    except Exception as e:
                        print(e)

                elif action =="graph_empleo":
                    try:
                        data={'title':''}
                        addUserData(request,data)
                        coordinaciones = Coordinacion.objects.filter(carrera__in=carreras).distinct()
                        aniosencuestas = EncuestaItb.objects.filter().values_list('fecharealizado__year',flat=True).distinct()
                        data['listanio'] = [{"anio": i} for i in aniosencuestas]
                        # CARRERA
                        data['lista_carreras_ingresoh'] = [{"carreranombre": str(c.nombre),
                                                           "data": [{"nombre": ih.nombre,
                                                                     "cantidad": EncuestaItb.objects.filter(ingresohogar=ih, carrera=c).count()
                                                                     } for ih in ingresoh]
                                                           } for c in carreras]

                        data['lista_coordinaciones_ingresoh'] = [{"coordnombre": str(c.nombre),
                                                                 "data": [{"nombre": ih.nombre,
                                                                           "cantidad": EncuestaItb.objects.filter(ingresohogar=ih,carrera__in=c.carrera.all()).count()
                                                                           } for ih in ingresoh]
                                                                 } for c in coordinaciones]

                        data['lista_ingresoh_resumen'] = [{"ingresohnombre": str(ih.nombre),
                                                          "cantidad": EncuestaItb.objects.filter(ingresohogar=ih).count()
                                                          } for ih in ingresoh]

                        data['lista_carreras_ingresop'] = [{"carreranombre": str(c.nombre),
                                                          "data": [{"nombre": ip.nombre,
                                                                    "cantidad": EncuestaItb.objects.filter(ingresopropio=ip, carrera=c).count()
                                                                    } for ip in ingresop]
                                                          } for c in carreras]

                        data['lista_coordinaciones_ingresop'] = [{"coordnombre": str(c.nombre),
                                                                    "data": [{"nombre": ip.nombre,
                                                                              "cantidad": EncuestaItb.objects.filter(ingresopropio=ip,carrera__in=c.carrera.all()).count()
                                                                              } for ip in ingresop]
                                                                    } for c in coordinaciones]

                        data['lista_ingresop_resumen'] = [{"ingresopnombre": str(ip.nombre),
                                                         "cantidad": EncuestaItb.objects.filter(ingresopropio=ip).count()
                                                         } for ip in ingresop]

                        data['lista_carreras_empleo'] = [{"carreranombre": str(c.nombre),
                                                              "data": [{"nombre": e.nombre,
                                                                        "cantidad": EncuestaItb.objects.filter(empleo=e, carrera=c).count()
                                                                        } for e in empleo]
                                                              } for c in carreras]

                        data['lista_coordinaciones_empleo'] = [{"coordnombre": str(c.nombre),
                                                                    "data": [{"nombre": e.nombre,
                                                                              "cantidad": EncuestaItb.objects.filter(empleo=e,carrera__in=c.carrera.all()).count()
                                                                              } for e in empleo]
                                                                    } for c in coordinaciones]

                        data['lista_empleo_resumen'] = [{"empleonombre": str(e.nombre),
                                                           "cantidad": EncuestaItb.objects.filter(empleo=e).count()
                                                           } for e in empleo]

                        data['listadocarreras'] = carreras
                        data['listcoordinaciones'] = coordinaciones
                        data['listingresoh'] = ingresoh
                        data['listingresop'] = ingresop
                        data['listempeo'] = empleo
                        return render(request, "cons_encuestaingreso/graf_empleos.html", data)
                    except Exception as e:
                        print(e)

                elif action =='graph_transporte':
                    try:
                        data = {'title': ''}
                        addUserData(request, data)
                        coordinaciones = Coordinacion.objects.filter(carrera__in=carreras).distinct()
                        aniosencuestas = EncuestaItb.objects.filter().values_list('fecharealizado__year',flat=True).distinct()
                        data['listanio'] = [{"anio": i} for i in aniosencuestas]
                        # CARRERA
                        data['lista_carreras_usotrasporte'] = [{"carreranombre": str(c.nombre),
                                                            "data": [{"nombre": ut.nombre,
                                                                      "cantidad": EncuestaItb.objects.filter(usotransporte=ut, carrera=c).count()
                                                                      } for ut in usotransporte]
                                                            } for c in carreras]

                        data['lista_coordinaciones_usotransporte'] = [{"coordnombre": str(c.nombre),
                                                                       "data": [{"nombre": ut.nombre,
                                                                                 "cantidad": EncuestaItb.objects.filter(usotransporte=ut,carrera__in=c.carrera.all()).count()
                                                                                } for ut in usotransporte]
                                                                  } for c in coordinaciones]

                        data['lista_usotransporte_resumen'] = [{"utrasportenombre": str(ut.nombre),
                                                           "cantidad": EncuestaItb.objects.filter(usotransporte=ut).count()
                                                           } for ut in usotransporte]

                        data['lista_carreras_tipotransporte']=[{"carreranombre": str(c.nombre),
                                                                "data": [{"nombre": t.nombre,
                                                                          "cantidad": EncuestaItb.objects.filter(transporte=t, carrera=c).count()
                                                                         } for t in tipotransporte]
                                                                } for c in carreras]

                        data['lista_coordinaciones_tipotransporte']=[{"coordnombre": str(c.nombre),
                                                                      "data": [{"nombre": t.nombre,
                                                                                "cantidad": EncuestaItb.objects.filter(transporte=t, carrera__in=c.carrera.all()).count()
                                                                                } for t in tipotransporte]
                                                                     } for c in coordinaciones]

                        data['lista_ttransporte_resumen'] = [{"ttrasportenombre": str(t.nombre),
                                                            "cantidad": EncuestaItb.objects.filter(transporte=t).count()
                                                           } for t in tipotransporte]
                        data['utrasporte']=usotransporte
                        data['ttrasporte']= tipotransporte
                        data['listadocarreras'] = carreras
                        data['listcoordinaciones'] = coordinaciones
                        return render(request, "cons_encuestaingreso/graf_transporte.html", data)
                    except Exception as e:
                        print(e)

                elif action =='graph_deportes':
                    try:
                        data = {'title': ''}
                        addUserData(request, data)
                        coordinaciones = Coordinacion.objects.filter(carrera__in=carreras).distinct()
                        aniosencuestas = EncuestaItb.objects.filter().values_list('fecharealizado__year',flat=True).distinct()
                        data['listanio'] = [{"anio": i} for i in aniosencuestas]
                        # CARRERA

                        data['lista_carreras_deportes']  = [{"carreranombre": str(c.nombre),
                                                                "data": [{"nombre": dep.nombre,
                                                                          "cantidad": EncuestaItb.objects.filter(deporte__contains=str(dep.pk), carrera=c).count()
                                                                          } for dep in deportes]
                                                                } for c in carreras]

                        data['lista_coordinaciones_deportes'] = [{"coordnombre": str(c.nombre),
                                                                       "data": [{"nombre": dep.nombre,
                                                                                 "cantidad": EncuestaItb.objects.filter(deporte__contains=str(dep.pk), carrera__in=c.carrera.all()).count()
                                                                                 } for dep in deportes]
                                                                       } for c in coordinaciones]

                        data['lista_deportes_resumen'] = [{"deportenombre": str(dep.nombre),
                                                                "cantidad": EncuestaItb.objects.filter(deporte__contains=str(dep.pk)).count()
                                                                } for dep in deportes]

                        data['lista_carreras_manifestaciones'] =[{"carreranombre":str(c.nombre),
                                                                 "data": [{"nombre": m.nombre,
                                                                           "cantidad": EncuestaItb.objects.filter(manifestacion=m,carrera=c).count()
                                                                           } for m in manifestaciones]
                                                                 } for c in carreras]

                        data['lista_coordinaciones_manifestaciones'] =[{"coordnombre": str(c.nombre),
                                                                       "data": [{"nombre": m.nombre,
                                                                                 "cantidad": EncuestaItb.objects.filter(manifestacion=m, carrera__in=c.carrera.all()).count()
                                                                                 } for m in manifestaciones]
                                                                       } for c in coordinaciones]

                        data['lista_manifestaciones_resumen']=[{"manifestacionnombre": str(m.nombre),
                                                                "cantidad": EncuestaItb.objects.filter(manifestacion=m).count()
                                                                } for m in manifestaciones]
                        data['deportes'] = deportes
                        data['manifestaciones'] = manifestaciones
                        data['listcarreras'] = carreras
                        data['listcoordinaciones'] = coordinaciones

                        return render(request, "cons_encuestaingreso/graf_deportes.html", data)
                    except Exception as ex:
                        print(ex)

            else:

                return render(request, "cons_encuestaingreso/cons_encuestaingreso.html", data)


    except Exception as e:
        print(e)
        return HttpResponseRedirect("/?info=Error comunicarse con el administrador ")
