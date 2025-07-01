from datetime import datetime,timedelta,time
from decimal import Decimal
import json
import string
import xlwt

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import RangoFacturasForm
from django.contrib.auth.models import User
from sga.models import convertir_fecha, TituloInstitucion, ReporteExcel, RubroEspecieValorada, GestionTramite, \
    SeguimientoEspecie, Coordinacion, Persona, SolicitudSecretariaDocente, IncidenciaAsignada, ViewTramites, \
    Inscripcion, ViewSolicitudes, Departamento
from sga.reportes import elimina_tildes

@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    try:
        if request.method=='POST':
            action = request.POST['action']
            if action == 'generarexcel':
                try:
                    inicio = request.POST['inicio']
                    fin = request.POST['fin']
                    fechai = convertir_fecha(inicio)
                    fechaf = convertir_fecha(fin)

                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                    titulo.font.height = 20*11
                    titulo2.font.height = 20*11
                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                    subtitulo.font.height = 20*10

                    cabecera_tabla1 = xlwt.easyxf('font: name Times New Roman, colour black, bold on; align: horiz center; borders: top thin, left thin, right thin, bottom thin')
                    cabecera_tabla2 = xlwt.easyxf('font: name Times New Roman, colour black, bold on; borders: top thin, bottom thin')
                    cabecera_tabla2_left = xlwt.easyxf('font: name Times New Roman, colour black, bold on; borders: top thin, bottom thin, left thin')
                    cabecera_tabla2_right = xlwt.easyxf('font: name Times New Roman, colour black, bold on; borders: top thin, bottom thin, right thin')
                    border_left = xlwt.easyxf('borders: left thin')
                    border_right = xlwt.easyxf('borders: right thin')

                    wb = xlwt.Workbook()

                    ws = wb.add_sheet('Gestionados', cell_overwrite_ok=True)
                    tit = TituloInstitucion.objects.all()[:1].get()
                    ws.write_merge(0, 0, 0, 17, tit.nombre, titulo2)
                    ws.write_merge(1, 1, 0, 17, 'Listado Tiempo de gestion por tramite en bandeja', titulo2)
                    ws.write(3, 0, 'DESDE: ', titulo)
                    ws.write(3, 1, inicio, titulo)
                    ws.write(4, 0, 'HASTA:', titulo)
                    ws.write(4, 1, fin, titulo)

                    ws.write_merge(6, 6, 0, 8, 'ALUMNO', cabecera_tabla1)
                    ws.write(7, 0, 'NOMBRE', cabecera_tabla2_left)
                    ws.write(7, 1, 'CEDULA', cabecera_tabla2)
                    ws.write(7, 2, 'CELULAR', cabecera_tabla2)
                    ws.write(7, 3, 'CONVENCIONAL', cabecera_tabla2)
                    ws.write(7, 4, 'CORREO PERSONAL', cabecera_tabla2)
                    ws.write(7, 5, 'CORREO INSTITUCIONAL', cabecera_tabla2)
                    ws.write(7, 6, 'GRUPO', cabecera_tabla2)
                    ws.write(7, 7, 'CARRERA', cabecera_tabla2)
                    ws.write(7, 8, 'FACULTAD', cabecera_tabla2_right)

                    ws.write_merge(6, 6, 9, 16, 'TRAMITE', cabecera_tabla1)
                    ws.write(7, 9, 'TIPO', cabecera_tabla2_left)
                    ws.write(7, 10, 'DIA', cabecera_tabla2_left)
                    ws.write(7, 11, 'MES', cabecera_tabla2)
                    ws.write(7, 12, 'ANIO', cabecera_tabla2)
                    ws.write(7, 13, '# DE TRAMITE', cabecera_tabla2)
                    ws.write(7, 14, 'REQUERIMIENTO', cabecera_tabla2)
                    ws.write(7, 15, 'DETALLE REQ/SOLIC.', cabecera_tabla2)
                    ws.write(7, 16, 'TIPO DE REQUERIMIENTO', cabecera_tabla2_right)

                    ws.write_merge(6, 6, 17, 24, 'RESPONSABLE', cabecera_tabla1)
                    ws.write(7, 17, 'FECHA ASIGNACION', cabecera_tabla2_left)
                    ws.write(7, 18, 'PERSONA RESPONSABLE', cabecera_tabla2)
                    ws.write(7, 19, 'DEPARTAMENTO', cabecera_tabla2)
                    ws.write(7, 20, 'TIEMPO GESTION(HORAS)', cabecera_tabla2)
                    ws.write(7, 21, 'OBSERVACION', cabecera_tabla2)
                    ws.write(7, 22, 'OBS. RESOLUCION', cabecera_tabla2)
                    ws.write(7, 23, 'ESTADO', cabecera_tabla2)
                    ws.write(7, 24, 'TOTAL HORAS', cabecera_tabla2_right)

                    from django.db import connection
                    cur = connection.cursor()
                    cur.execute("REFRESH MATERIALIZED VIEW view_tramites; REFRESH MATERIALIZED VIEW view_solicitudes;")
                    try:
                        connection.commit()
                    except Exception as e:
                        print("Error al actualizar la vista materializada view_tramites:", str(e))
                        connection.rollback()

                    fila = 8
                    tramites = ViewTramites.objects.filter(fecha__range=(fechai, fechaf)).order_by('rubroespecie_id', 'fecha', 'fecha_asignacion')
                    if request.POST['departamento'] != '0':
                        tramites = tramites.filter(departamento_id = request.POST['departamento'])
                    for tramite in tramites:
                        tiempo_total = ViewTramites.objects.filter(rubroespecie_id=tramite.rubroespecie_id).aggregate(Sum('tiempo'))['tiempo__sum']
                        rubro_especie = RubroEspecieValorada.objects.get(pk=tramite.rubroespecie_id)
                        inscripcion = Inscripcion.objects.get(id=tramite.inscripcion_id)
                        coordinacion = ''
                        if Coordinacion.objects.filter(carrera=inscripcion.carrera).exists():
                            coordinacion = Coordinacion.objects.filter(carrera=inscripcion.carrera)[:1].get().nombre
                        # Inscripcion
                        ws.write(fila, 0, elimina_tildes(inscripcion.persona.nombre_completo_inverso()), border_left)
                        ws.write(fila, 1, inscripcion.persona.cedula if inscripcion.persona.cedula else inscripcion.persona.pasaporte)
                        ws.write(fila, 2, inscripcion.persona.telefono if inscripcion.persona.telefono else '')
                        ws.write(fila, 3, inscripcion.persona.telefono_conv if inscripcion.persona.telefono_conv else '')
                        ws.write(fila, 4, inscripcion.persona.email if inscripcion.persona.email else '')
                        ws.write(fila, 5, inscripcion.persona.emailinst)
                        ws.write(fila, 6, inscripcion.grupo().nombre)
                        ws.write(fila, 7, inscripcion.carrera.nombre)
                        ws.write(fila, 8, coordinacion, border_right)

                        # Tramite
                        ws.write(fila, 9, 'ESPECIE')
                        ws.write(fila, 10, str(tramite.fecha.day))
                        ws.write(fila, 11, str(tramite.fecha.month))
                        ws.write(fila, 12, str(tramite.fecha.year))
                        ws.write(fila, 13, tramite.serie)
                        ws.write(fila, 14, tramite.observacion_alumno)
                        ws.write(fila, 15, tramite.observacion)
                        ws.write(fila, 16, tramite.tipo_especie, border_right)

                        #Responsable
                        ws.write(fila, 17, str(tramite.fecha_asignacion))
                        ws.write(fila, 18, elimina_tildes(tramite.persona_asignada))
                        ws.write(fila, 19, tramite.departamento)
                        ws.write(fila, 20, tramite.tiempo)
                        ws.write(fila, 21, tramite.observacion)
                        ws.write(fila, 22, tramite.resolucion)
                        ws.write(fila, 23, 'FINALIZADA' if rubro_especie.aplicada else 'HABILITADA')
                        ws.write(fila, 24, tiempo_total, border_right)
                        fila += 1

                    solicitudes = ViewSolicitudes.objects.filter(fecha__range=(fechai, fechaf)).order_by('solicitud_id', 'fecha', 'fecha_asignacion')
                    if request.POST['departamento'] != '0':
                        solicitudes = solicitudes.filter(departamento_id = request.POST['departamento'])
                    for solicitud in solicitudes:
                        tiempo_total = ViewSolicitudes.objects.filter(solicitud_id=solicitud.solicitud_id).aggregate(Sum('tiempo'))['tiempo__sum']
                        # Inscripcion
                        ws.write(fila, 0, solicitud.nombre_inscripcion, border_left)
                        ws.write(fila, 1, solicitud.identificacion_inscripcion)
                        ws.write(fila, 2, solicitud.celular if solicitud.celular else '')
                        ws.write(fila, 3, solicitud.convencional if solicitud.convencional else '')
                        ws.write(fila, 4, solicitud.email if solicitud.email else '')
                        ws.write(fila, 5, solicitud.emailinst)
                        ws.write(fila, 6, solicitud.grupo)
                        ws.write(fila, 7, solicitud.carrera)
                        ws.write(fila, 8, solicitud.facultad, border_right)

                        # Tramite
                        ws.write(fila, 9, 'SOLICITUD')
                        ws.write(fila, 10, str(solicitud.fecha.day))
                        ws.write(fila, 11, str(solicitud.fecha.month))
                        ws.write(fila, 12, str(solicitud.fecha.year))
                        ws.write(fila, 13, solicitud.solicitud_id)
                        ws.write(fila, 14, solicitud.solicitud)
                        ws.write(fila, 15, solicitud.observacion)
                        ws.write(fila, 16, solicitud.tipo_solicitud, border_right)

                        # Responsable
                        ws.write(fila, 17, str(solicitud.fecha_asignacion))
                        ws.write(fila, 18, elimina_tildes(solicitud.persona_asignada))
                        ws.write(fila, 19, solicitud.departamento)
                        ws.write(fila, 20, solicitud.tiempo)
                        ws.write(fila, 21, solicitud.observacion)
                        ws.write(fila, 22, solicitud.resolucion if solicitud.resolucion else '')
                        ws.write(fila, 23, 'FINALIZADA' if solicitud.finalizada else 'HABILITADA')
                        ws.write(fila, 24,  tiempo_total, border_right)
                        fila += 1

                    # tramites = RubroEspecieValorada.objects.filter(rubro__fecha__range=(fechai, fechaf), rubro__cancelado=True, aplicada=True)\
                    #     .order_by('fecha', 'rubro__inscripcion__persona__apellido1', 'rubro__inscripcion__persona__apellido2')
                    #     # .exclude(fechafinaliza=None)\
                    #
                    # fila = 8
                    # for tramite in tramites:
                    #     # print(tramite.serie)
                    #     tiempo_docente = 0
                    #     existe = False
                    #     contador = 0
                    #     fila_autoriza = None
                    #     tiempo_autorizada = 0
                    #     if SeguimientoEspecie.objects.filter(rubroespecie=tramite).exclude(asistente=None).exclude(fechaasig=None).exists():
                    #         existe = True
                    #         seguimiento = SeguimientoEspecie.objects.filter(rubroespecie=tramite).exclude(asistente=None).exclude(fechaasig=None).order_by('id')
                    #         contador += seguimiento.count()
                    #         for s in seguimiento:
                    #             tiempo = (datetime.combine(s.fecha, s.hora) - s.fechaasig).total_seconds() / 3600
                    #             ws.write(fila, 16, str(s.fechaasig.date()))
                    #             ws.write(fila, 17, elimina_tildes(Persona.objects.filter(usuario=s.asistente)[:1].get().nombre_completo_inverso()))
                    #             ws.write(fila, 18, elimina_tildes(s.departamento()))
                    #             ws.write(fila, 19, str(round(tiempo, 2)))
                    #             ws.write(fila, 20, elimina_tildes(s.observacion))
                    #             ws.write(fila, 21, "")
                    #             ws.write(fila, 22, "", border_right)
                    #
                    #             if tramite.usrautoriza == s.asistente:
                    #                 fila_autoriza = fila
                    #                 tiempo_autorizada = tiempo
                    #
                    #             fila += 1
                    #
                    #     if GestionTramite.objects.filter(tramite=tramite).exclude(fecharespuesta=None).exclude(fechaasignacion=None).exists():
                    #         existe = True
                    #         tramite_docente = GestionTramite.objects.filter(tramite=tramite).exclude(fecharespuesta=None).exclude(fechaasignacion=None)
                    #         contador += tramite_docente.count()
                    #         for t in tramite_docente:
                    #             tiempo = (t.fecharespuesta - t.fechaasignacion).total_seconds() / 3600
                    #             tiempo_docente += tiempo
                    #             ws.write(fila, 16, str(t.fechaasignacion.date()))
                    #             ws.write(fila, 17, elimina_tildes(t.profesor.nombre_completo_inverso()).encode('utf-8'))
                    #             ws.write(fila, 18, "DOCENTE")
                    #             ws.write(fila, 19, str(round(tiempo, 2)))
                    #             ws.write(fila, 20, elimina_tildes(t.respuesta).encode('utf-8'))
                    #             ws.write(fila, 21, "")
                    #             ws.write(fila, 22, "", border_right)
                    #
                    #             fila += 1
                    #
                    #     fila = fila - contador if contador > 0 else fila
                    #     contador = contador if contador > 0 else 1
                    #     if existe:
                    #         contador += 1
                    #     for x in range(contador):
                    #         alumno = tramite.rubro.inscripcion.persona
                    #         coordinacion = ''
                    #         if Coordinacion.objects.filter(carrera=tramite.rubro.inscripcion.carrera).exists():
                    #             coordinacion = Coordinacion.objects.filter(carrera=tramite.rubro.inscripcion.carrera)[:1].get().nombre
                    #
                    #         # Informacion del alumno
                    #         ws.write(fila, 0, alumno.nombre_completo_inverso().encode('utf-8'), border_left)
                    #         ws.write(fila, 1, alumno.cedula if alumno.cedula else alumno.pasaporte)
                    #         ws.write(fila, 2, alumno.telefono if alumno.telefono else '')
                    #         ws.write(fila, 3, alumno.telefono_conv if alumno.telefono_conv else '')
                    #         ws.write(fila, 4, alumno.email if alumno.email else '')
                    #         ws.write(fila, 5, alumno.emailinst)
                    #         ws.write(fila, 6, tramite.rubro.inscripcion.grupo().nombre)
                    #         ws.write(fila, 7, tramite.rubro.inscripcion.carrera.nombre)
                    #         ws.write(fila, 8, coordinacion, border_right)
                    #
                    #         obsestudiante=''
                    #         try:
                    #             if tramite.es_online().observacion:
                    #                 obsestudiante= (elimina_tildes(tramite.es_online().observacion)).replace(","," ").replace(":","").replace("%"," ").replace("\ "," ")
                    #         except:
                    #             pass
                    #
                    #         # Informacion del tramite
                    #         ws.write(fila, 9, str(tramite.rubro.fecha.day), border_left)
                    #         ws.write(fila, 10, str(tramite.rubro.fecha.month))
                    #         ws.write(fila, 11, str(tramite.rubro.fecha.year))
                    #         ws.write(fila, 12, str(tramite.serie))
                    #         ws.write(fila, 13, 'TRAMITE')
                    #         ws.write(fila, 14, obsestudiante.encode('utf-8'))
                    #         ws.write(fila, 15, elimina_tildes(tramite.tipoespecie.nombre), border_right)
                    #
                    #         if contador == x+1:
                    #             # Responsable
                    #             fecha_asigna = tramite.fechaasigna if tramite.fechaasigna else datetime.combine(tramite.rubro.fecha, time.max)
                    #             fecha_finaliza = tramite.fechafinaliza if tramite.fechafinaliza else datetime.now()
                    #             tiempo = (fecha_finaliza - fecha_asigna).total_seconds() / 3600
                    #             if tiempo_docente > 0 and not fila_autoriza:
                    #                 tiempo -= tiempo_docente
                    #             ws.write(fila, 16, str(tramite.fechaasigna.date() if tramite.fechaasigna else ""), border_left)
                    #             ws.write(fila, 17, elimina_tildes(Persona.objects.filter(usuario=tramite.usrasig)[:1].get().nombre_completo_inverso()))
                    #             ws.write(fila, 18, elimina_tildes(tramite.departamento))
                    #             ws.write(fila, 19, str(round(tiempo, 2)))
                    #             printable_chars = set(string.printable)
                    #             observaciones = (''.join(filter(lambda x: x in printable_chars, tramite.observaciones))) if tramite.observaciones else ""
                    #             obs_autoriza = (''.join(filter(lambda x: x in printable_chars, tramite.obsautorizar))) if tramite.obsautorizar else ""
                    #             ws.write(fila, 20, observaciones) #ERROR AQUI
                    #             ws.write(fila, 21, str(tramite.usrautoriza) if tramite.usrautoriza else "" + " - " + obs_autoriza) #ERROR AQUI
                    #
                    #             if fila_autoriza and tiempo_docente > 0:
                    #                 tiempo = tiempo_autorizada - tiempo_docente
                    #                 ws.write(fila_autoriza, 19, str(round(tiempo, 2)))
                    #
                    #         ws.write(fila, 22, "FINALIZADO" if not tramite.disponible else "En PROCESO", border_right)
                    #         fila += 1
                    #
                    # SOLICITUDES
                    # solicitudes = SolicitudSecretariaDocente.objects.filter(fecha__range=(fechai, fechaf), asignado=True).order_by('fecha','id').exclude(solicitudestudiante=None)
                    # for solicitud in solicitudes:
                    #     # print(solicitud.id)
                    #     contador = 1
                    #     incidencia = None
                    #     if IncidenciaAsignada.objects.filter(solicitusecret=solicitud).exclude(fecha=None).exclude(fechaasig=None).exists():
                    #         incidencias = IncidenciaAsignada.objects.filter(solicitusecret=solicitud).exclude(fecha=None).order_by('id')
                    #         contador += incidencias.count()
                    #         for incidencia in incidencias:
                    #             # ws.write(fila, 22, "INCIDENCIA")
                    #             # ws.write(fila, 23, "INCIDENCIA")
                    #             ws.write(fila, 17, elimina_tildes(Persona.objects.filter(usuario=incidencia.usuario)[:1].get().nombre_completo_inverso()))
                    #             ws.write(fila, 18, elimina_tildes(incidencia.asistentedepartamento.departamento.descripcion))
                    #             if incidencia.fechaasig:
                    #                 tiempo = (incidencia.fecha - incidencia.fechaasig).total_seconds() / 3600
                    #                 ws.write(fila, 16, str(incidencia.fechaasig.date()))
                    #                 ws.write(fila, 19, str(round(tiempo, 2)))
                    #             else:
                    #                 ws.write(fila, 19, "GESTION")
                    #
                    #             ws.write(fila, 20, elimina_tildes(incidencia.observacion))
                    #             ws.write(fila, 21, "")
                    #             ws.write(fila, 22, "", border_right)
                    #             fila += 1
                    #
                    #     fila = (fila - contador+1) if contador>1 else fila
                    #     for x in range(contador):
                    #         alumno = solicitud.solicitudestudiante.inscripcion.persona
                    #         coordinacion = ''
                    #         if Coordinacion.objects.filter(carrera=solicitud.solicitudestudiante.inscripcion.carrera).exists():
                    #             coordinacion = Coordinacion.objects.filter(carrera=solicitud.solicitudestudiante.inscripcion.carrera)[:1].get().nombre
                    #
                    #         # Informacion del alumno
                    #         ws.write(fila, 0, alumno.nombre_completo_inverso(), border_left)
                    #         ws.write(fila, 1, alumno.cedula if alumno.cedula else alumno.pasaporte)
                    #         ws.write(fila, 2, alumno.telefono if alumno.telefono else '')
                    #         ws.write(fila, 3, alumno.telefono_conv if alumno.telefono_conv else '')
                    #         ws.write(fila, 4, alumno.email if alumno.email else '')
                    #         ws.write(fila, 5, alumno.emailinst)
                    #         ws.write(fila, 6, solicitud.solicitudestudiante.inscripcion.grupo().nombre)
                    #         ws.write(fila, 7, solicitud.solicitudestudiante.inscripcion.carrera.nombre)
                    #         ws.write(fila, 8, coordinacion, border_right)
                    #
                    #         # Informacion del tramite
                    #         ws.write(fila, 9, str(solicitud.fecha.day), border_left)
                    #         ws.write(fila, 10, str(solicitud.fecha.month))
                    #         ws.write(fila, 11, str(solicitud.fecha.year))
                    #         ws.write(fila, 12, solicitud.id)
                    #         ws.write(fila, 13, 'SOLICITUD')
                    #         printable_chars = set(string.printable)
                    #         descripcion = (''.join(filter(lambda x: x in printable_chars, solicitud.descripcion))).encode('ascii', 'ignore') if solicitud.descripcion else ""
                    #         ws.write(fila, 14, elimina_tildes(descripcion))
                    #         ws.write(fila, 15, elimina_tildes(solicitud.tipo.nombre), border_right)
                    #         ws.write(fila, 22, "", border_right)
                    #         # ws.write(fila, 24, solicitud.id, border_right)
                    #         fila += 1
                    #     fila -= 1
                    #
                    #     # Responsable
                    #     # if incidencia:
                    #
                    #     ws.write(fila, 16, str(solicitud.fechaasignacion.date()))
                    #     ws.write(fila, 17, elimina_tildes(Persona.objects.filter(usuario=solicitud.usuario)[:1].get().nombre_completo_inverso()))
                    #     ws.write(fila, 18, elimina_tildes(solicitud.departamento.descripcion) if solicitud.departamento else "")
                    #     if solicitud.fechacierre:
                    #         fecha = datetime.combine(solicitud.fechacierre, solicitud.hora)
                    #         tiempo = (fecha - solicitud.fechaasignacion).total_seconds() / 3600
                    #         ws.write(fila, 19, str(round(tiempo, 2)))
                    #     else:
                    #         ws.write(fila, 19, "EN PROCESO")
                    #     printable_chars = set(string.printable)
                    #     # observaciones = (''.join(filter(lambda x: x in printable_chars, solicitud.observacion))).encode('ascii', 'ignore') if solicitud.observacion else ""
                    #     observaciones = (''.join(filter(lambda x: x in printable_chars, solicitud.observacion))).encode('utf-8', 'ignore') if solicitud.observacion else ""
                    #     ws.write(fila, 20, elimina_tildes(observaciones))
                    #     ws.write(fila, 21, "")
                    #     ws.write(fila, 22, "", border_right)
                    #     # ws.write(fila, 23, "POSI")
                    #     # ws.write(fila, 24, str(solicitud.id))
                    #     fila+=1

                    fila += 1
                    ws.write(fila, 0, "Fecha Impresion", subtitulo)
                    ws.write(fila, 1, str(datetime.now()), subtitulo)
                    ws.write(fila+1, 0, "Usuario", subtitulo)
                    ws.write(fila+1, 1, str(request.user), subtitulo)

                    nombre ='bandejagestion'+str(datetime.now()).replace(" ","").replace(".","").replace(":","")+'.xls'
                    wb.save(MEDIA_ROOT+'/reporteexcel/'+nombre)
                    return HttpResponse(json.dumps({"result":"ok", "url": "/media/reporteexcel/"+nombre}),content_type="application/json")

                except Exception as ex:
                    print(str(ex))
                    return HttpResponse(json.dumps({"result":'bad', 'mensaje':str(ex)}),content_type="application/json")
        else:
            data = {'title': 'Listado de Gestion de Tiempos en Solicitudes y Tramites'}
            addUserData(request,data)
            if ReporteExcel.objects.filter(activo=True,vista=request.path[1:]).exists():
                data['hoy'] = datetime.now().date()
                data['departamentos'] = Departamento.objects.filter(controlespecies=True).order_by('descripcion')
                return render(request ,"reportesexcel/tiempo_tramites_bandeja.html" ,  data)
            return HttpResponseRedirect("/reporteexcel")

    except Exception as e:
        return HttpResponseRedirect('/?info='+str(e))

