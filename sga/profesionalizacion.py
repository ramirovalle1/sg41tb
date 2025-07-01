import json
from datetime import datetime, timedelta
import os
from django.contrib.auth.models import User

import xlwt
from django.contrib.admin.models import LogEntry, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.utils.encoding import force_str
from sga.tasks import send_html_mail

from django.db import transaction

from sga.reportes import elimina_tildes
from sga.commonviews import  ip_client_address,addUserData
from decorators import secure_module
from sga.models import Inscripcion, Rubro, Persona, \
    Carrera,Grupo,Nivel,TituloInstitucion,Matricula, \
    Periodo, Coordinacion,InscripcionProfesionalizacion, GrupoCoordinadorCarrera
from sga.forms import AprobacionProfesionalizacionForm

from settings import MEDIA_ROOT, EMAIL_ACTIVE

def convertir_fecha(s):
    return datetime(int(s[6:10]), int(s[3:5]), int(s[0:2])).date()

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
    hoy = datetime.today().date()
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action=='aprobacion':
                try:
                    estado_aprobacion=str(request.POST['estado'])
                    observacion = elimina_tildes(request.POST['observacion'])
                    resolucion = elimina_tildes(request.POST['resolucion'])
                    if InscripcionProfesionalizacion.objects.filter(inscripcion=request.POST['inscripcion']).exists():
                        inscripprof=InscripcionProfesionalizacion.objects.filter(inscripcion=request.POST['inscripcion'])[:1].get()
                        carrera=inscripprof.inscripcion.carrera
                        coordinacion= Coordinacion.objects.filter(carrera=carrera)[:1].get()
                        personarespon = Persona.objects.filter(usuario=request.user)[:1].get()
                        personarespon=elimina_tildes(personarespon.nombre_completo_inverso())
                        data={}
                        inscripprof.observacion=observacion.upper()
                        inscripprof.resolucion=resolucion.upper()
                        inscripprof.fecha=datetime.now()
                        inscripprof.usuario=request.user
                        inscripprof.save()
                        if estado_aprobacion=='0':
                            inscripprof.aprobacion=False
                            inscripprof.save()
                            correo=coordinacion.correo+','+str(inscripprof.inscripcion.persona.emailinst)+','+str(inscripprof.inscripcion.persona.email)
                            hoy = datetime.now().today()
                            if EMAIL_ACTIVE:
                                send_html_mail("NO APROBACION ENTREVISTA PROFESIONALIZACION",
                                "emails/correo_entrevistaprofesionalizacion.html", {'contenido':"ENTREVISTA NO HA SIDO APROBADA",'obs':observacion,'estudiante':str(inscripprof.inscripcion.persona.nombre_completo_inverso()),'resol':resolucion,'personarespon':personarespon,'carrera':elimina_tildes(inscripprof.inscripcion.carrera.nombre),'fecha':hoy,'estado':estado_aprobacion},correo.split())
                            data = {"result": "ok"}
                            return HttpResponse(json.dumps(data),content_type="application/json")
                        else:
                            inscripprof.aprobacion=True
                            inscripprof.save()
                            correo=coordinacion.correo+','+str(inscripprof.inscripcion.persona.emailinst)+','+str(inscripprof.inscripcion.persona.email)
                            hoy = datetime.now().today()
                            if EMAIL_ACTIVE:
                                send_html_mail("APROBACION ENTREVISTA PROFESIONALIZACION",
                                "emails/correo_entrevistaprofesionalizacion.html", {'contenido':"ENTREVISTA HA SIDO APROBADA",'obs':observacion,'estudiante':elimina_tildes(inscripprof.inscripcion.persona.nombre_completo_inverso()),'resol':resolucion,'personarespon':personarespon,'carrera':elimina_tildes(inscripprof.inscripcion.carrera.nombre),'fecha':hoy,'estado':estado_aprobacion},correo.split())
                            data = {"result": "ok"}
                            return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as ex:
                    print(ex)
                    datos = {"result": "bad"}
                    return HttpResponse(json.dumps(datos),content_type="application/json")

            if action == 'generarexcel':
                try:
                    if request.POST['paralelo'] == 'true':
                        if Nivel.objects.filter(pk=request.POST['nivel']).exists():
                            nivel = Nivel.objects.filter(pk=request.POST['nivel'])[:1].get()
                            inscripcion = Inscripcion.objects.filter(carrera__maestria=True,
                                                                     matricula__nivel=nivel).order_by('persona__apellido1',
                                                                                                      'persona__apellido2',
                                                                                                      'persona__nombres')
                    else:
                        inscripcion = Inscripcion.objects.filter(carrera__maestria=True).order_by(
                            'persona__apellido1',
                            'persona__apellido2',
                            'persona__nombres')

                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on;align: vert centre')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20 * 11
                    titulo2.font.height = 20 * 11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20 * 10
                    m = 0
                    wb = xlwt.Workbook()
                    ws = wb.add_sheet('Listado', cell_overwrite_ok=True)

                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0, 0, 6, tit.nombre, titulo2)
                    ws.write_merge(1, 1, 0, m + 2, 'ESTUDIANTES INSCRITOS EN MAESTRIA ', titulo2)

                    ws.write(4, 0, "# INSCRITOS: ", titulo)
                    if request.POST['paralelo'] == 'true':
                        if Nivel.objects.filter(pk=request.POST['nivel']).exists():
                            nivel = Nivel.objects.filter(pk=request.POST['nivel'])[:1].get()
                            ws.write(5, 0, "PARALELO: ", titulo)
                            ws.write(5, 1, nivel.paralelo)

                    fila = 6
                    ws.write(fila, 0, "NOMBRE", titulo)
                    ws.write(fila, 1, "MAESTRIA", titulo)
                    ws.write(fila, 2, "GRUPO/NIVEL", titulo)
                    ws.write(fila, 3, "PERIODO", titulo)
                    ws.write(fila, 4, "CEDULA", titulo)
                    ws.write(fila, 5, "TELEFONO", titulo)
                    ws.write(fila, 6, "TELEFONO CONVENCIONAL", titulo)
                    ws.write(fila, 7, "EMAIL", titulo)
                    ws.write(fila, 8, "TUTOR", titulo)

                    ws.write(fila, 9, "TIENE ENTREVISTA ", titulo)
                    ws.write(fila, 10, "ENTREVISTA APROBADA", titulo)
                    ws.write(fila, 11, "NUEVA ENTREVISTA ", titulo)
                    ws.write(fila, 12, "USUARIO QUE REALIZO LA INSCRIPCION", titulo)
                    ws.write(fila, 13, "TURNO PARA ENTREVISTA ", titulo)
                    ws.write(fila, 14, "PAGO MATRICULA", titulo)
                    ws.write(fila, 15, "CANTIDAD DE CUOTAS", titulo)
                    ws.write(fila, 16, "CANTIDAD DE CUOTAS PAGADAS", titulo)
                    ws.write(fila, 17, "VIDEO SUBIDO", titulo)

                    # ws.write(fila, 14, "PAGO MATRICULA ", titulo)


                    fila = 7
                    for m in inscripcion:
                        matricula=None
                        try:
                            persona =  elimina_tildes(m.persona.nombre_completo_inverso())
                        except:
                            persona = 'ERROR EN NOMBRE'
                        ws.write(fila, 0,persona)

                        if m.carrera:
                            ws.write(fila, 1, m.carrera.nombre)
                        else:
                            ws.write(fila, 1, '')
                        if m.grupo():
                            if Matricula.objects.filter(inscripcion=m).exists():
                                matricula = Matricula.objects.filter(inscripcion=m)[:1].get()
                                ws.write(fila, 2,  elimina_tildes(matricula.nivel) )
                            else:
                                ws.write(fila, 2, m.grupo().nombre )
                        else:
                            ws.write(fila, 2, '')
                        if matricula:
                            ws.write(fila, 3, elimina_tildes(matricula.nivel.periodo))
                        if m.persona.cedula:
                            ws.write(fila, 4, m.persona.cedula)
                        else:
                            ws.write(fila, 4, '')

                        if m.persona.telefono:
                            ws.write(fila, 5, m.persona.telefono)
                        else:
                            ws.write(fila, 5, '')
                        if m.persona.telefono_conv:
                            ws.write(fila, 6, m.persona.telefono_conv)
                        else:
                            ws.write(fila, 6, '')
                        if m.persona.email:
                            ws.write(fila, 7, m.persona.email)
                        else:
                            ws.write(fila, 7, '')
                        if m.tiene_tutor():
                            ws.write(fila, 8, m.tiene_tutor().tutor.persona.nombre_completo())
                        else:
                            ws.write(fila, 8, '')
                        if m.tiene_entrevista():
                            ws.write(fila, 9, "SI")
                            if m.tiene_entrevista().aprobacion:
                                ws.write(fila, 10, "SI")
                            else:
                                ws.write(fila, 10, 'NO')
                        else:
                            ws.write(fila, 9, 'NO')
                        if m.tiene_entrevista():
                            if m.tiene_entrevista().entrevista:
                                ws.write(fila,11,'SI')
                            else:
                                ws.write(fila,11,'NO')


                        if m.userinscribe:
                            ws.write(fila, 12, m.userinscribe.username)
                        else:
                            ws.write(fila, 12, '')
                        # if DetalleTurnoFecha.objects.filter(inscripcion=m).exists():
                        #     detalle=DetalleTurnoFecha.objects.filter(inscripcion=m)[:1].get()
                        #     ws.write(fila, 13, str(detalle.fechaturno.fecha))
                        # else:
                        #     ws.write(fila, 13, 'NO TIENE TURNO')
                        if Matricula.objects.filter(inscripcion=m).exists():
                            matricula = Matricula.objects.filter(inscripcion=m)[:1].get()
                            if Rubro.objects.filter(inscripcion=m, inscripcion__carrera__maestria=True, inscripcion__matricula=matricula,cancelado=True,pagonivel__tipo__matricula=True).exists():
                                # rubro=Rubro.objects.filter(inscripcion=m, inscripcion__carrera__maestria=True,inscripcion__matricula=matricula, cancelado=True, tiporubro__id=3)[:1].get()
                                ws.write(fila,14, 'SI')
                                # ws.write(fila,13, 'SI')
                            else:
                                ws.write(fila,14,'NO')
                        else:
                            ws.write(fila, 14, 'NO MATRICULADO')

                        cantrubro=Rubro.objects.filter(inscripcion=m ,pagonivel__tipo__cuota=True).count()
                        cantrubropag=Rubro.objects.filter(inscripcion=m ,pagonivel__tipo__cuota=True,cancelado=True).count()
                        ws.write(fila, 15, cantrubro)

                        ws.write(fila, 16, cantrubropag)
                        if m.archvideo:
                            ws.write(fila, 17, 'SI')
                        else:
                            ws.write(fila, 17, 'NO')

                        fila = fila+1

                    nombre = 'estudiantesmaestria' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":","") + '.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    # wb.save('C:/cyolo_ube/ube/ube/media/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/ube/media/reporteexcel/"+nombre,"acc":request.POST['acc']}), content_type="application/json")

                except Exception as ex:
                        print('ERROR: '+str(ex))
                        return HttpResponse(json.dumps({"result":str(ex)+" "+str(m)}), content_type="application/json")



    else:
        data = {'title': 'Listado de Aspirantes Profesionalizacion'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
        else:
            try:
                search = None
                carreras=None
                gruposc = None
                if User.objects.filter(pk=request.user.id,groups__id__in=[1,2,17,83]).exists():
                    gruposcoord=User.objects.filter(pk=request.user.id,groups__id__in=[1,2,17,83]).values('groups')
                    carreras= GrupoCoordinadorCarrera.objects.filter(group__id__in=gruposcoord,carrera__validacionprofesional=True).order_by('id').values('carrera')
                    # print(carreras)

                else:
                    carreras=Carrera.objects.filter(pk__in=carreras).order_by('nombre')
                if 'carrera' in request.GET:
                    c=Carrera.objects.filter(id=request.GET['carrera'])[:1].get()
                    carreras = Carrera.objects.filter(id=c.id).order_by('nombre')
                    data['carrera']=c

                if 's' in request.GET:
                    search = request.GET['s']
                    if search !='':
                        ss = search.split(' ')
                        while '' in ss:
                            ss.remove('')
                        if len(ss) == 1:
                            if gruposc:
                                inscripciones = Inscripcion.objects.filter(Q(persona__nombres__icontains=search) | Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search) | Q(persona__cedula__icontains=search) | Q(persona__pasaporte__icontains=search) | Q(identificador__icontains=search) | Q(inscripciongrupo__grupo__nombre__icontains=search) | Q(carrera__nombre__icontains=search) | Q(persona__usuario__username__icontains=search),inscripciongrupo__grupo__in=gruposc,carrera__validacionprofesional=True,carrera__in=carreras,persona__usuario__is_active=True).order_by('persona__apellido1')[:100]
                            else:
                                inscripciones = Inscripcion.objects.filter(Q(persona__nombres__icontains=search)|Q(persona__apellido1__icontains=search)|Q(persona__apellido2__icontains=search)|Q(persona__cedula__icontains=search)|Q(persona__pasaporte__icontains=search)|Q(carrera__alias__icontains=search)| Q(inscripciongrupo__grupo__nombre__icontains=search),carrera__validacionprofesional=True,carrera__in=carreras,persona__usuario__is_active=True).order_by('-fecha','persona__apellido1')
                        else:
                            if gruposc:
                                inscripciones = Inscripcion.objects.filter(Q(persona__apellido1__icontains=ss[0])&Q(persona__apellido2__icontains=ss[1]),carrera__validacionprofesional=True,inscripciongrupo__grupo__in=gruposc,carrera__in=carreras,persona__usuario__is_active=True).order_by('-fecha','persona__apellido1','persona__apellido2','persona__nombres')
                            else:
                                inscripciones = Inscripcion.objects.filter(Q(persona__apellido1__icontains=ss[0])&Q(persona__apellido2__icontains=ss[1]),carrera__validacionprofesional=True,carrera__in=carreras,persona__usuario__is_active=True).order_by('-fecha','persona__apellido1','persona__apellido2','persona__nombres')

                    else:
                        if gruposc:
                           inscripciones = Inscripcion.objects.filter(inscripciongrupo__grupo__in=gruposc,persona__usuario__is_active=True,carrera__in=carreras,carrera__validacionprofesional=True).order_by('persona__apellido1','persona__apellido2','persona__nombres')
                        else:
                           inscripciones = Inscripcion.objects.filter(persona__usuario__is_active=True,pk__in=Inscripcion.objects.filter(persona__usuario__is_active=True,carrera__in=carreras,carrera__validacionprofesional=True).values('pk')[:100]).order_by('persona__apellido1','persona__apellido2','persona__nombres')

                else:
                    inscripciones = Inscripcion.objects.filter(carrera__validacionprofesional=True,carrera__in=carreras,persona__usuario__is_active=True).order_by('carrera__nombre','persona__nombres','-fecha')

                if 'op' in request.GET:
                    if request.GET['op']=='1':
                        ins=InscripcionProfesionalizacion.objects.filter().values('inscripcion')
                        inscripciones = inscripciones.filter(id__in=ins)
                    data['op']= request.GET['op']

                if 'g' in request.GET:
                    grupoid = request.GET['g']
                    data['grupo'] = Grupo.objects.get(pk=request.GET['g'])
                    data['grupoid'] = int(grupoid) if grupoid else ""
                    if gruposc:
                        inscripciones =  Inscripcion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(),carrera__validacionprofesional=True,inscripciongrupo__grupo=data['grupo']).distinct()
                    else:
                        inscripciones =  Inscripcion.objects.filter(carrera__grupocoordinadorcarrera__group__in=request.user.groups.all(),carrera__validacionprofesional=True,inscripciongrupo__grupo=data['grupo']).distinct()

                paging = MiPaginador(inscripciones, 30)
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
                data['search'] = search if search else ""
                data['gruposc'] = gruposc if gruposc else ""
                if gruposc:
                    data['grupos'] = Grupo.objects.filter(id__in=gruposc).order_by('nombre')
                else:
                    data['grupos'] = Grupo.objects.filter(carrera__validacionprofesional=True,carrera__in=carreras).order_by('nombre')
                data['inscripciones'] = page.object_list
                if 'error' in request.GET:
                    data['error']= request.GET['error']
                data['carreras']=Carrera.objects.filter(validacionprofesional=True)
                data['form']=AprobacionProfesionalizacionForm()
                data['periodos'] = Periodo.objects.filter(id__in=Nivel.objects.filter(carrera__validacionprofesional=True).values('periodo')).order_by('inicio')

                return render(request ,"profesionalizacion/profesionalizacion.html" ,  data)

            except Exception as e:
                print(e)
                return HttpResponseRedirect("/profesionalizacion")