#Embedded file name: ./templatetags/sga_extras.py
from datetime import date, timedelta, datetime
import json
from django import template
from django.db.models import Q
from django.http import HttpResponse
from sga.models import MESES_CHOICES, Actividad
from sga.reportes import elimina_tildes

register = template.Library()

def callMethod(obj, methodName):
    method = getattr(obj, methodName)
    if hasattr(obj, '__callArg'):
        ret = method(*obj.__callArg)
        del obj.__callArg
        return ret
    return method()


def args(obj, arg):
    if not '__callArg' in obj.__dict__:
        obj.__dict__['__callArg'] = []
    obj.__callArg.append(arg)
    return obj


def suma(var, value = 1):
    return var + value


def divide(value, arg):
    return int(value) / int(arg)


def calendarbox(var, dia):
    return var[dia]


def barraporciento(var, total):
    if int(total) == 0:
        return 0
    else:
        return int(var) / 5 * int(total)


def calendarboxdetails(var, dia):
    return var[dia]



def accioncalendar(request):
    # ////////////////////////////// CALENDARIO NUEVO /////////////////////////
    try:
        data={}
        fecha = datetime.now().date()
        panio = fecha.year
        pmes = fecha.month
        if 'accion' in request.POST:
            action = request.POST['accion']
            if action == 'anterior':
                mes = int(request.POST['mes'])
                anio = int(request.POST['anio'])
                pmes = mes - 1
                if pmes == 0:
                    pmes = 12
                    panio = anio - 1
                else:
                    panio = anio
            elif action == 'proximo':
                mes = int(request.POST['mes'])
                anio = int(request.POST['anio'])
                pmes = mes + 1
                if pmes == 13:
                    pmes = 1
                    panio = anio + 1
                else:
                    panio = anio

        fechainicio = date(panio, pmes, 1)
        try:
            fechafin = date(panio, pmes, 31)
        except:
            try:
                fechafin = date(panio, pmes, 30)
            except:
                try:
                    fechafin = date(panio, pmes, 29)
                except:
                    fechafin = date(panio, pmes, 28)

        actividades = Actividad.objects.filter(Q(inicio__lte=fechainicio) & Q(fin__gte=fechainicio) | Q(inicio__lte=fechafin) & Q(fin__gte=fechafin) | Q(inicio__lte=fechainicio) & Q(fin__gte=fechafin) | Q(inicio__gte=fechainicio) & Q(fin__lte=fechafin)).order_by('id')
        s_anio = panio
        s_mes = pmes
        s_dia = 1
        data['mes'] = MESES_CHOICES[s_mes - 1][1]
        ws = [0,7,14,21,28,35]
        lista = {}
        listaactividades = {}
        for i in range(1, 43, 1):
            dia = {i: 'no'}
            actividaddia = {i: None}
            lista.update(dia)
            listaactividades.update(actividaddia)

        comienzo = False
        fin = False
        num = 0
        bandecal = 0
        mesesanterior = {}
        mesvaria=''
        actividadesdet={}
        for i in lista.items():
            try:
                bandecal = bandecal + 1
                fecha = date(s_anio, s_mes, s_dia)
                if fecha.isoweekday() == i[0] and fin is False and comienzo is False:
                    comienzo = True
                else:
                    if not comienzo:

                        bancal = 0
                        diamen = 1
                        while ( bancal < 1):
                            fecha = date(s_anio, s_mes, s_dia) - timedelta(diamen)
                            if fecha.isoweekday() == i[0]:
                                num = fecha.day
                                bancal = 1
                                diamen = 0
                            else:
                                diamen =  diamen + 1
                                num = 0
            except:
                num = num + 1
                bandeano=0
                if s_mes+1 == 13:
                    bandeano=1
                    fecha = date(s_anio+1, 1, num)
                else:
                    if bandeano == 1:
                        fecha = date(s_anio+1, s_mes+1, num)
                    else:
                        fecha = date(s_anio, s_mes+1, num)
                pass

            if comienzo:
                try:
                    fecha = date(s_anio, s_mes, s_dia)
                except:
                    fin = True

            if comienzo and fin is False:
                dia = {i[0]: s_dia}
                s_dia += 1
                lista.update(dia)
                actividadesdias = Actividad.objects.filter(Q(inicio__lte=fecha) & Q(fin__gte=fecha)).order_by('id')
                diaact = []
                actividaddet = []
                for actividad in actividadesdias:
                    diasemana = fecha.isoweekday()
                    adicionar = False
                    if diasemana == 1 and actividad.lunes == True:
                        adicionar = True
                    if diasemana == 2 and actividad.martes == True:
                        adicionar = True
                    if diasemana == 3 and actividad.miercoles == True:
                        adicionar = True
                    if diasemana == 4 and actividad.jueves == True:
                        adicionar = True
                    if diasemana == 5 and actividad.viernes == True:
                        adicionar = True
                    if diasemana == 6 and actividad.sabado == True:
                        adicionar = True
                    if diasemana == 7 and actividad.domingo == True:
                        adicionar = True
                    if adicionar:
                        act = actividad.tipo.representacion
                        diaact.append(act)
                        if actividad.responsable:
                            nombreresponsable=str(elimina_tildes(actividad.responsable.nombre_completo()))
                        else:
                            nombreresponsable = None
                        adicional = ''
                        if actividad.adicional:
                            adicional = actividad.adicional
                        lugar = ''
                        if actividad.lugar:
                            lugar = actividad.lugar
                        elif actividad.auditorio:
                            lugar = actividad.auditorio.nombre
                        actividaddet.append(actividad.nombre+"_Desde: "+str(actividad.inicio)+"_Hasta: "+str(actividad.fin)+"_Hora Inicio: "+str(actividad.horainicio)+"_Hora Fin: "+str(actividad.horafin)+"_Responsable: "+str(nombreresponsable)+"_Lugar: "+lugar+"_Informacion Adicional: "+(adicional))
                listaactividades.update({i[0]: diaact})
                actividadesdet.update({i[0]: actividaddet})

                mesvaria={i[0]: 'no'}
            else:
                dia = {i[0]: num}
                if num > 25:
                    num = 0
                lista.update(dia)
                actividadesdias = Actividad.objects.filter(Q(inicio__lte=fecha) & Q(fin__gte=fecha)).order_by('id')
                diaact = []
                actividaddet = []
                for actividad in actividadesdias:
                    diasemana = fecha.isoweekday()
                    adicionar = False
                    if diasemana == 1 and actividad.lunes == True:
                        adicionar = True
                    if diasemana == 2 and actividad.martes == True:
                        adicionar = True
                    if diasemana == 3 and actividad.miercoles == True:
                        adicionar = True
                    if diasemana == 4 and actividad.jueves == True:
                        adicionar = True
                    if diasemana == 5 and actividad.viernes == True:
                        adicionar = True
                    if diasemana == 6 and actividad.sabado == True:
                        adicionar = True
                    if diasemana == 7 and actividad.domingo == True:
                        adicionar = True
                    if adicionar:
                        act = actividad.tipo.representacion
                        diaact.append(act)
                        if actividad.responsable:
                            nombreresponsable=str(elimina_tildes(actividad.responsable.nombre_completo()))
                        else:
                            nombreresponsable = None
                        adicional = ''
                        if actividad.adicional:
                            adicional = actividad.adicional
                        actividaddet.append(actividad.nombre+"_Desde: "+str(actividad.inicio)+"_Hasta: "+str(actividad.fin)+"_Hora Inicio: "+str(actividad.horainicio)+"_Hora Fin: "+str(actividad.horafin)+"_Responsable: "+str(nombreresponsable)+"_Lugar: "+(actividad.lugar)+"_Informacion Adicional "+(adicional))

                listaactividades.update({i[0]: diaact})
                actividadesdet.update({i[0]: actividaddet})

                mesvaria = {i[0]: 'si'}
            mesesanterior.update(mesvaria)


        data['dwnm'] =[{"diacon": str(t) } for t in  ['lunes','martes','miercoles','jueves','viernes','sabado','domingo'] ]
        dwn = [1,2,3,4,5,6,7]
        data['daymonth'] = 1
        data['s_anio'] = s_anio
        data['s_mes'] = s_mes
        box=[]
        infobox=[]
        for w in ws:
            for dw in dwn:
                try:
                    dia = int(w) + int(dw)
                except :
                    try:
                        dia = w + dw
                    except:
                        dia = w

                box.append([calendarbox(lista,dia),dw,calendarboxdetails(listaactividades,dia),calendarboxdetails(actividadesdet,dia),str(mesesanterior[dia])])
                infobox.append(calendarboxdetails(listaactividades,dia))
        # print([{"boxdia": str(x[0]),"diase":str(x[1]),"infobox":x[2],"acti":x[3],"mesanterior":x[4]  } for x in box])
        data["box"]=[{"boxdia": str(x[0]),"diase":str(x[1]),"infobox":x[2],"acti":x[3],"mesanterior":x[4]  } for x in box]
        data["infobox"]= [{"info": str(y) } for y in infobox]
        data['result'] = "ok"

        return HttpResponse(json.dumps(data),content_type="application/json")
    except Exception as ex:
        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")


#Ids ManyToMany para los templates
def many_to_many_values(obj, field_name):
    return list(getattr(obj, field_name).values_list('id', flat=True))


def extraer(campo, cantidad):
    return campo[0:cantidad]


register.filter('call', callMethod)
register.filter('args', args)
register.filter('suma', suma)
register.filter('divide', divide)
register.filter('calendarbox', calendarbox)
register.filter('calendarboxdetails', calendarboxdetails)
register.filter('barraporciento', barraporciento)
register.filter('many_to_many_values', many_to_many_values)
register.filter("extraer", extraer)



