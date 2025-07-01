# -*- coding: latin-1 -*-
import json
from datetime import datetime
import os
import smtplib
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION, DELETION
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from django.template import RequestContext
import xlwt
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from settings import REPORTE_CRONOGRAMA_PROFESOR, EMAIL_ACTIVE, VALIDA_MATERIA_APROBADA, DEFAULT_PASSWORD, SITE_ROOT, EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import ClaseOnlineForm, MaterialDocenteForm, MaterialDocenteEditarForm
from sga.models import Profesor, Materia, MateriaAsignada, TipoIncidencia,Persona, LogAceptacionProfesorMateria, ProfesorMateria, LeccionGrupo, Coordinacion, \
     elimina_tildes, ClasesOnline, convertir_fecha,Leccion, TituloInstitucion,Clase, MaterialDocente, TipoMaterialDocente, Nee
from sga.tasks import send_html_mail
from socioecon.cons_socioecon import ip_client_address


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    if request.method == 'POST':
        action = request.POST['action']
        if action == 'correomasivo':
           try:
                materia =Materia.objects.get(id = request.POST['idmat'])
                alumnos = MateriaAsignada.objects.filter(materia=materia)
                result = {}
                result['result'] ="ok"
                result['totales']="0"
                result['turno']  ="0"
                lista = []
                cont = 0
                usuario = request.user
                user=Profesor.objects.get(persona__usuario=usuario)
                for alumno in alumnos:
                    if alumno.matricula.inscripcion.persona.emailinst:
                        if cont == 0:
                            cont=1
                            lista.append([alumno.matricula.inscripcion.persona.emailinst])
                        else:
                            lista[0][0]=str(lista[0][0])+','+str(alumno.matricula.inscripcion.persona.emailinst)

                if EMAIL_ACTIVE:
                    # lista.append([])
                    mail_correoprofe(request.POST['contenido'],request.POST['asunto'],str(lista[0][0]), request.user)
                return HttpResponse(json.dumps(result),content_type="application/json")
           except:
                return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        elif action =='addclaseonline':
            pm = ProfesorMateria.objects.filter(pk=request.POST['id'])[:1].get()
            try:
                f= ClaseOnlineForm(request.POST)
                if f.is_valid():
                    if int(request.POST['idclase']) > 0:
                        clasesonline=ClasesOnline.objects.filter(pk=int(request.POST['idclase']))[:1].get()
                        clasesonline.fecha=(f.cleaned_data['fecha'])
                        clasesonline.url=f.cleaned_data['url']
                        clasesonline.save()
                        mensaje ='Editada'
                    else:
                        clasesonline = ClasesOnline(profesormateria=pm,
                                                    fecha=(f.cleaned_data['fecha']),
                                                    url=f.cleaned_data['url'])
                        clasesonline.save()
                        mensaje ='Adicionada'
                    client_address = ip_client_address(request)

                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(clasesonline).pk,
                        object_id       = clasesonline.id,
                        object_repr     = force_str(clasesonline),
                        action_flag     = ADDITION,
                        change_message  = mensaje + ' Clase Online (' + client_address + ')' )
                    return HttpResponseRedirect('/pro_cronograma?action=online&idma='+str(pm.materia.id))
            except Exception as e:
                return HttpResponseRedirect('/pro_cronograma?error='+str(e))





        elif action == 'rechazarmateria':
           try:

                    materia =Materia.objects.get(id = int(request.POST['idmateria']))
                    profesor=Profesor.objects.get(id = int(request.POST['idprofesor']))
                    tipolog = int(request.POST['tipolog'])
                    result = {}
                    result['result'] ="ok"
                    lista=[]
                    if ProfesorMateria.objects.filter(id=int(request.POST['id']), materia=materia,profesor=profesor).exists():
                        profesormateria =ProfesorMateria.objects.get(id=int(request.POST['id']),materia=materia,profesor=profesor)
                    else:
                        profesormateria =ProfesorMateria.objects.get(id=int(request.POST['id']),materia=materia,profesor_aux=profesor.id)

                    if profesormateria.profesor_aux:
                        profesor = Profesor.objects.get(pk=profesormateria.profesor_aux)
                    else:
                        profesor = profesormateria.profesor
                    if LeccionGrupo.objects.filter(profesor=profesor,materia=profesormateria.materia,abierta=True).exists():
                        return HttpResponse(json.dumps({"result":"bad","fechamayor":3}),content_type="application/json")


                    if str(datetime.now().date()) <= str(profesormateria.hasta):
                        num=LogAceptacionProfesorMateria.objects.count()+1
                        logaceptacion= LogAceptacionProfesorMateria(id=num,materia=materia,
                                                            profesor = profesor,
                                                            fechaceptacion = datetime.now(),
                                                            aceptacion=True if tipolog==1 else False,
                                                            tipolog=tipolog,
                                                            profesormateria=profesormateria,
                                                            oberservacion=request.POST['comentario'])
                        logaceptacion.save()



                        profesormateria.aceptacion=False
                        profesormateria.idzoom=""

                        client_address = ip_client_address(request)
                        # LOG DE CAMBIAR FECHA MATREIA
                        LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(profesormateria).pk,
                        object_id       = profesormateria.id,
                        object_repr     = force_str(profesormateria),
                        action_flag     = ADDITION,
                        change_message  = 'RECHAZO LA MATERIA (' + client_address + ')' )


                        profesormateria.save()

                        if Coordinacion.objects.filter(carrera=profesormateria.materia.nivel.carrera).exists():
                             correo = Coordinacion.objects.filter(carrera=profesormateria.materia.nivel.carrera)[:1].get().correo+','+'soporteitb@bolivariano.edu.ec'
                             #correo = 'soporteitb@bolivariano.edu.ec'
                        else:
                            correo = 'soporteitb@bolivariano.edu.ec'
                        if EMAIL_ACTIVE:

                                #mail_correoprofeacepta('EL DOCENTE NO ACEPTO LA MATERIA','NO ACEPTACION DE MATERIA','floresvillamarinm@gmail.com',materia,profesor,request.user,profesormateria,logaceptacion.oberservacion)
                                mail_correoprofeacepta('EL DOCENTE NO ACEPTO LA MATERIA','NO ACEPTACION DE MATERIA',str(profesor.persona.emailinst)+','+str(correo),materia,profesor,request.user,profesormateria,logaceptacion.oberservacion)
                        return HttpResponse(json.dumps(result),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad","fechamayor":1}),content_type="application/json")
           except Exception as ex:
                print(ex)
                return HttpResponse(json.dumps({"result":"bad","fechamayor":0}),content_type="application/json")

        elif action == 'aceptarrechazarmateria':
           try:

                f = MaterialDocenteForm(request.POST,request.FILES)
                if f.is_valid():

                    materia =Materia.objects.get(id = int(request.POST['idmateria']))
                    profesor=Profesor.objects.get(id = int(request.POST['idprofesor']))
                    tipolog = int(request.POST['tipolog'])
                    result = {}
                    result['result'] ="ok"

                    if ProfesorMateria.objects.filter(id=int(request.POST['idprosmateria']), materia=materia,profesor=profesor).exists():
                        profesormateria =ProfesorMateria.objects.get(id=int(request.POST['idprosmateria']),materia=materia,profesor=profesor)
                    else:
                        profesormateria =ProfesorMateria.objects.get(id=int(request.POST['idprosmateria']),materia=materia,profesor_aux=profesor.id)

                    if profesormateria.profesor_aux:
                        profesor = Profesor.objects.get(pk=profesormateria.profesor_aux)
                    else:
                        profesor = profesormateria.profesor
                    if LeccionGrupo.objects.filter(profesor=profesor,materia=profesormateria.materia,abierta=True).exists():

                        # return HttpResponseRedirect('/pro_cronograma?error:'+'No puede rechazar la materia porque tiene clase iniciada')
                        return HttpResponse(json.dumps({"result": "bad", "mensaje": "No puede aceptar/rechazar la materia porque tiene clase abierta"}), content_type="application/json")

                    if str(datetime.now().date()) <= str(profesormateria.hasta):

                        logaceptacion= LogAceptacionProfesorMateria(materia=materia,
                                                            profesor = profesor,
                                                            fechaceptacion = datetime.now(),
                                                            aceptacion=True if tipolog==1 else False,
                                                            tipolog=tipolog,
                                                            profesormateria=profesormateria,
                                                            oberservacion=request.POST['comentario'])
                        logaceptacion.save()

                        if tipolog==1:
                            profesormateria.aceptacion=True
                            profesormateria.idzoom=request.POST['idzoom']

                            client_address = ip_client_address(request)
                            # LOG DE CAMBIAR FECHA MATREIA
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(profesormateria).pk,
                            object_id       = profesormateria.id,
                            object_repr     = force_str(profesormateria),
                            action_flag     = ADDITION,
                            change_message  = 'ACEPTO LA MATERIA (' + client_address + ')' )

                        else:
                            profesormateria.aceptacion=False

                            client_address = ip_client_address(request)
                            # LOG DE CAMBIAR FECHA MATREIA
                            LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(profesormateria).pk,
                            object_id       = profesormateria.id,
                            object_repr     = force_str(profesormateria),
                            action_flag     = ADDITION,
                            change_message  = 'RECHAZO LA MATERIA (' + client_address + ')' )

                        profesormateria.save()

                        if 'material' in request.FILES:
                            material = request.FILES['material']

                            tipomaterial=TipoMaterialDocente.objects.get(id=1)

                            if MaterialDocente.objects.filter(materia=materia,
                                                            profesor = profesor,profesormateria=profesormateria,tipomaterial=tipomaterial).exists():

                               materialdocente = MaterialDocente.objects.get(materia=materia,
                                                            profesor = profesor,profesormateria=profesormateria,tipomaterial=tipomaterial)

                               materialdocente.archivo=material



                            else:
                                materialdocente=MaterialDocente(materia=materia,
                                                                profesor = profesor,
                                                                fecha = datetime.now(),
                                                                archivo=material,
                                                                tipomaterial_id=1,
                                                                profesormateria=profesormateria,
                                                                aprobado=False
                                                                )

                            materialdocente.save()

                        if 'bancopregunta' in request.FILES:
                            bancodocentedoc = request.FILES['bancopregunta']

                            tipomaterial=TipoMaterialDocente.objects.get(id=2)

                            if MaterialDocente.objects.filter(materia=materia,
                                                            profesor = profesor,profesormateria=profesormateria,tipomaterial=tipomaterial).exists():

                                bancodocente=MaterialDocente.objects.get(materia=materia,
                                                            profesor = profesor,profesormateria=profesormateria,tipomaterial=tipomaterial)


                                bancodocente.archivo=bancodocentedoc

                            else:

                                bancodocente=MaterialDocente(materia=materia,
                                                                profesor = profesor,
                                                                fecha = datetime.now(),
                                                                archivo=bancodocentedoc,
                                                                tipomaterial_id=2,
                                                                profesormateria=profesormateria,
                                                                aprobado=False
                                                                )
                            bancodocente.save()

                        if Coordinacion.objects.filter(carrera=profesormateria.materia.nivel.carrera).exists():
                             correo = (Coordinacion.objects.filter(carrera=profesormateria.materia.nivel.carrera)[:1].get().correo)+','+'soporteitb@bolivariano.edu.ec'
                             #correo = 'soporteitb@bolivariano.edu.ec'
                        else:
                            correo = 'soporteitb@bolivariano.edu.ec'

                        if EMAIL_ACTIVE:
                             try:
                                 if tipolog==1:
                                    lista=[]
                                #     mail_correoprofeacepta('EL DOCENTE ACEPTO LA MATERIA','ACEPTACION DE MATERIA','floresvillamarinm@gmail.com',materia,profesor,request.user,profesormateria,logaceptacion.oberservacion)
                                    materiasasiganda= MateriaAsignada.objects.filter(materia=profesormateria.materia).distinct('matricula__inscripcion').order_by('matricula__inscripcion__persona__apellido1','matricula__inscripcion__persona__apellido2','matricula__inscripcion__persona__nombres')
                                    # materiasasiganda= MateriaAsignada.objects.filter(matricula__inscripcion__id=79253, materia=profesormateria.materia).distinct('matricula__inscripcion').order_by('matricula__inscripcion__persona__apellido1','matricula__inscripcion__persona__apellido2','matricula__inscripcion__persona__nombres')
                                    materia = Materia.objects.filter(pk=materia.id)[:1].get()
                                    titulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                                    titulo2 = xlwt.easyxf('font: bold on; align: wrap on, vert centre, horiz center')
                                    titulo.font.height = 20*11
                                    titulo2.font.height = 20*11
                                    subtitulo = xlwt.easyxf('font: name Times New Roman, colour black, bold on')
                                    subtitulo3 = xlwt.easyxf('font: name Times New Roman; align: wrap on, vert centre, horiz center')
                                    subtitulo4 = xlwt.easyxf('font: name Times New Roman, colour blue')
                                    subtitulo.font.height = 20*10
                                    wb = xlwt.Workbook()
                                    ws = wb.add_sheet('Registros',cell_overwrite_ok=True)

                                    tit = TituloInstitucion.objects.all()[:1].get()
                                    ws.write(0, 1, 'INSTITUTO TECNOLOGICO BOLIVARIANO', titulo)
                                    ws.write(1, 1, 'LISTADO ALUMNOS MATRICULADOS', titulo)
                                    ws.write(3, 0,'CARRERA: ' +materia.nivel.carrera.nombre , subtitulo)
                                    ws.write(4, 0,'GRUPO:   ' +materia.nivel.grupo.nombre, subtitulo)
                                    ws.write(5, 0,'NIVEL:   ' +materia.nivel.nivelmalla.nombre, subtitulo)

                                    fila = 7
                                    col = 0
                                    informe=''
                                    documento=None
                                    origen=''
                                    ws.write(fila-1, col, "ALUMNO", titulo)
                                    ws.write(fila-1, col+1, "CORREO INSTITUCIONAL", titulo)
                                    for matsasi in materiasasiganda:
                                        # print(matsasi)
                                        ws.write(fila, col,elimina_tildes(matsasi.matricula.inscripcion.persona.nombre_completo_inverso()))
                                        ws.write(fila, col+1,elimina_tildes(matsasi.matricula.inscripcion.persona.emailinst))
                                        if Nee.objects.filter(inscripcion=matsasi.matricula.inscripcion).exists():
                                            informe=Nee.objects.filter(inscripcion=matsasi.matricula.inscripcion)[:1].get()

                                            if len(str(informe.resumen))>0:
                                                documento=informe.resumen
                                                origen = 'https://sga.itb.edu.ec/media/'+str(documento)
                                                ws.write(fila,col+2, xlwt.Formula('HYPERLINK("'+origen+'")'),subtitulo4)
                                                lista.append((elimina_tildes(matsasi.matricula.inscripcion.persona.nombre_completo_inverso()), origen))
                                        fila = fila + 1
                                    cont = fila + 3
                                    if informe != '':
                                        if len(str(informe.resumen))>0:
                                            #21-02-2022 adjuntar correo de RGarcia cuando hay informe DOBE
                                            ws.write(6, col+2, "INFORME DISCAPACIDAD", titulo)
                                            emaildobe= TipoIncidencia.objects.get(pk=70).correo
                                            contenidodobe='Estudiante(s) con discapacidad e informe entregado a docente'
                                            asuntodobe='INFORME DISCAPACIDAD'
                                            profmat=profesormateria
                                            profesormateria.documentaciondiscapacidad=True
                                            profesormateria.save()
                                            mail_dobe(contenidodobe,asuntodobe,profmat,emaildobe,lista,request.user)

                                    ws.write(cont, 0, "Fecha Impresion", subtitulo)
                                    ws.write(cont, 2, str(datetime.now()), subtitulo)
                                    cont = cont + 1
                                    ws.write(cont, 0, "Usuario", subtitulo)
                                    ws.write(cont, 2, str(request.user), subtitulo)

                                    nombre = 'listadoestudiantes' + str(datetime.now()).replace(" ", "").replace(".", "").replace(":","") + '.xls'
                                    carpeta = MEDIA_ROOT + '/reportes_excel/'
                                    try:
                                        os.makedirs(carpeta)
                                    except:
                                        pass
                                    wb.save(carpeta + nombre)

                                    if Clase.objects.filter(materia__profesormateria__profesor=profesor,materia=materia).exists():
                                        clase = Clase.objects.filter(materia__profesormateria__profesor=profesor,materia=materia)[:1].get()
                                    else:
                                        clase=''

                                    mail_enviarlistadoalumnosmatriculado(nombre,'EL DOCENTE ACEPTO LA MATERIA','ACEPTACION DE MATERIA',materia,profesor,request.user,profesormateria,logaceptacion.oberservacion,str(profesor.persona.emailinst)+','+str(correo),clase,lista)

                                     # mail_correoprofeacepta('EL DOCENTE ACEPTO LA MATERIA','ACEPTACION DE MATERIA',str(profesor.persona.emailinst)+','+str(correo),materia,profesor,request.user,profesormateria,logaceptacion.oberservacion)
                                 else:
                                    #mail_correoprofeacepta('EL DOCENTE NO ACEPTO LA MATERIA','NO ACEPTACION DE MATERIA','floresvillamarinm@gmail.com',materia,profesor,request.user,profesormateria,logaceptacion.oberservacion)
                                    mail_correoprofeacepta('EL DOCENTE NO ACEPTO LA MATERIA','NO ACEPTACION DE MATERIA',str(profesor.persona.emailinst)+','+str(correo),materia,profesor,request.user,profesormateria,logaceptacion.oberservacion)
                             except Exception as e:
                                 print("error " +str(e))
                                 pass

                        return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
                    else:
                       return HttpResponse(json.dumps({"result": "bad","mensaje":"La fecha es mayor a la fecha de finalizacion de la materia"}),content_type="application/json")
                else:
                    return HttpResponse(json.dumps({"result": "bad","mensaje":"error el formato de uno de los archivo no es el correcto"}),content_type="application/json")
           except Exception as ex:
                print("error2 " + str(ex))
                return HttpResponse(json.dumps({"result": "bad","mensaje":ex}),content_type="application/json")



        elif action == 'editarmaterialdocente':
           try:

                f = MaterialDocenteEditarForm(request.POST,request.FILES)
                if f.is_valid():

                    materia =Materia.objects.get(id = int(request.POST['idmateriaedit']))
                    profesor=Profesor.objects.get(id = int(request.POST['idprofesoredit']))
                    result = {}
                    result['result'] ="ok"



                    if ProfesorMateria.objects.filter(id=int(request.POST['idprofesormateriaid']), materia=materia,profesor=profesor).exists():
                        profesormateria =ProfesorMateria.objects.get(id=int(request.POST['idprofesormateriaid']),materia=materia,profesor=profesor)
                    else:
                        profesormateria =ProfesorMateria.objects.get(id=int(request.POST['idprofesormateriaid']),materia=materia,profesor_aux=profesor.id)

                    if profesormateria.profesor_aux:
                        profesor = Profesor.objects.get(pk=profesormateria.profesor_aux)
                    else:
                        profesor = profesormateria.profesor
                    if LeccionGrupo.objects.filter(profesor=profesor,materia=profesormateria.materia,abierta=True).exists():

                        # return HttpResponseRedirect('/pro_cronograma?error:'+'No puede rechazar la materia porque tiene clase iniciada')
                        return HttpResponse(json.dumps({"result": "bad", "mensaje": "No puede editar material porque tiene clase abierta"}), content_type="application/json")

                    if 'materialeditar' in request.FILES:
                        material = request.FILES['materialeditar']

                        tipomaterial=TipoMaterialDocente.objects.get(id=1)

                        if MaterialDocente.objects.filter(materia=materia,
                                                        profesor = profesor,profesormateria=profesormateria,tipomaterial=tipomaterial).exists():

                           materialdocente = MaterialDocente.objects.get(materia=materia,
                                                        profesor = profesor,profesormateria=profesormateria,tipomaterial=tipomaterial)

                           materialdocente.archivo=material



                        else:
                            materialdocente=MaterialDocente(materia=materia,
                                                            profesor = profesor,
                                                            fecha = datetime.now(),
                                                            archivo=material,
                                                            tipomaterial_id=1,
                                                            profesormateria=profesormateria,
                                                            aprobado=False
                                                            )

                        materialdocente.save()

                    if 'bancopreguntaeditar' in request.FILES:
                        bancodocentedoc = request.FILES['bancopreguntaeditar']

                        tipomaterial=TipoMaterialDocente.objects.get(id=2)

                        if MaterialDocente.objects.filter(materia=materia,
                                                        profesor = profesor,profesormateria=profesormateria,tipomaterial=tipomaterial).exists():

                            bancodocente=MaterialDocente.objects.get(materia=materia,
                                                        profesor = profesor,profesormateria=profesormateria,tipomaterial=tipomaterial)


                            bancodocente.archivo=bancodocentedoc

                        else:

                            bancodocente=MaterialDocente(materia=materia,
                                                            profesor = profesor,
                                                            fecha = datetime.now(),
                                                            archivo=bancodocentedoc,
                                                            tipomaterial_id=2,
                                                            profesormateria=profesormateria,
                                                            aprobado=False
                                                            )
                        bancodocente.save()

                    return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")

                else:
                    return HttpResponse(json.dumps({"result": "bad","mensaje":"error el formato de uno de los archivo no es el correcto"}),content_type="application/json")
           except Exception as ex:
                print(ex)

                return HttpResponse(json.dumps({"result": "bad","mensaje":ex}),content_type="application/json")






        elif action == 'add_idzoom':
            try:
                result = {}
                result['result'] ="ok"
                profesormateria =  ProfesorMateria.objects.filter(pk=request.POST['id'])[:1].get()
                profesormateria.idzoom = request.POST['idzoom']
                profesormateria.save()
                return HttpResponseRedirect('/pro_cronograma')
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect('/pro_cronograma?error:'+ex)

    else:
        data = {'title': 'Cronograma de Materias del Profesor'}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'online':
                data['title'] = 'Registro de Clases Online'
                materia= Materia.objects.filter(pk=request.GET['idma'])[:1].get()
                profesor = Profesor.objects.get(persona__usuario=request.user)
                pm = ProfesorMateria.objects.filter(profesor=profesor,materia=materia)[:1].get()
                data['pm']=pm
                clasesonline = ClasesOnline.objects.filter(profesormateria=pm)
                data['clasesonline'] = clasesonline
                return render(request ,"pro_cronograma/clasesonline.html" ,  data)
            elif action == 'add':
                data['title'] = 'Adicionar Registro de Clases Online'
                pm = ProfesorMateria.objects.filter(pk=request.GET['pm'])[:1].get()
                form = ClaseOnlineForm(initial={'fecha':datetime.now().date()})
                data['pm'] = pm
                data['form'] = form
                data['edit'] = 0

                return render(request ,"pro_cronograma/addclaseonline.html" ,  data)
            elif action == 'eliminar':
                if ClasesOnline.objects.filter(pk=request.GET['idc']).exists():
                    claseonline = ClasesOnline.objects.filter(pk=request.GET['idc'])[:1].get()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(claseonline).pk,
                        object_id       = claseonline.id,
                        object_repr     = force_str(claseonline),
                        action_flag     = DELETION,
                        change_message  = 'Eliminada Clase Online (' + client_address + ')' )
                    idmateria = claseonline.profesormateria.materia.id
                    claseonline.delete()
                    return HttpResponseRedirect('/pro_cronograma?action=online&idma='+str(idmateria))

            elif action == 'edit':
                data['title'] = 'Editar Registro de Clases Online'
                clasesonline = ClasesOnline.objects.filter(pk=request.GET['idc'])[:1].get()
                data['pm'] = clasesonline.profesormateria
                initial = model_to_dict(clasesonline)
                form = ClaseOnlineForm(initial=initial)
                data['form'] = form
                data['edit'] = clasesonline.id
                return render(request ,"pro_cronograma/addclaseonline.html" ,  data)
                # return render(request ,"pro_cronograma/addclaseonline.html" ,  data)


            elif action=='detallearch':
                data = {}
                data['vermaterialdocente'] = MaterialDocente.objects.filter(profesormateria__id=request.GET['id']).order_by('fecha')

                return render(request ,"pro_cronograma/detallearchivbec.html" ,  data)



        else:
            if 'error' in request.GET:
                data['error'] = request.GET['error']


            periodo = request.session['periodo']
            ret = None
            if 'ret' in request.GET:
                ret = request.GET['ret']

            if 'id' in request.GET:
                profesor = Profesor.objects.get(pk=request.GET['id'])
            else:
                profesor = Profesor.objects.get(persona=data['persona'])

            if profesor.materias_imparte_sinperiodo():
                materias = profesor.materias_imparte_sinperiodo().order_by('inicio','nivel__sede')

                data['periodo'] = periodo
                data['profesor'] = profesor
                data['materias'] = materias
                data['DEFAULT_PASSWORD']=DEFAULT_PASSWORD
                data['ret'] = ret if ret else ""
                data['reporte_cronograma_profesor'] = REPORTE_CRONOGRAMA_PROFESOR
                data['VALIDA_MATERIA_APROBADA'] = VALIDA_MATERIA_APROBADA
                data['formMaterialDocente'] = MaterialDocenteForm
                data['MaterialDocenteEditarForm'] = MaterialDocenteEditarForm






                return render(request ,"pro_cronograma/materiasbs.html" ,  data)

            else:
                return HttpResponseRedirect("/?info=No tiene Materias en el periodo, SELECCIONE OTRO PERIODO")

def mail_correoprofe(contenido,asunto,email,user):
        hoy = datetime.now().today()
        persona = Persona.objects.get(usuario=user)
        send_html_mail(str(asunto),"emails/correoalumno.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'persona':persona},email.split(","))

def mail_correoprofeacepta(contenido,asunto,email,materia,profesor,user,profesormateria,observacion):
        hoy = datetime.now().today()
        send_html_mail(str(asunto),"emails/correoaceptacion.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'persona':profesor.persona,'materia':materia,'profesormateria':profesormateria,'observacion':observacion},email.split(","))

def mail_dobe(contenido,asunto,profesor,email,lista,user):
        hoy = datetime.now().today()
        send_html_mail(str(asunto),"emails/correoaceptacionmateriadobe.html", {'fecha': hoy,"user":user,'contenido': contenido, 'asunto': asunto,'profesormateria':profesor,'lista':lista},email.split(","))


def mail_enviarlistadoalumnosmatriculado(nombre,asunto,contenido,materia,profesor,usuario,profesormateria,observacion,emaillis,clase,lista):


    smtp_server = 'smtp.gmail.com:587'
    smtp_user = 'sgaitb@itb.edu.ec'
    smtp_pass = 'sgaitb2013$'
    email = MIMEMultipart()
    email['To'] = 'sgaitb@itb.edu.ec'
    email['From'] = 'sgaitb@itb.edu.ec'
    email['Subject'] = asunto
    aula=''
    listadiscapacidad='<table class="table" border="1px"> <thead ><tr><th style="background-color: #49afcd;text-align: center;width: 20%"><h3>Estudiante</h3></th><th style="background-color: #49afcd;text-align: center;width: 20%"><h3>Informe</h3></th></tr></thead>'
    if lista:
        listadiscapacidad=listadiscapacidad+'<tbody>'
        for l in lista:
            listadiscapacidad=listadiscapacidad+'<tr>'
            listadiscapacidad=listadiscapacidad+'<td>'+l[0]+'</td>'
            listadiscapacidad=listadiscapacidad+'<td>'+l[1]+'</td>'
            listadiscapacidad=listadiscapacidad+'</tr>'
        listadiscapacidad=listadiscapacidad+'</tbody></table>'
    else:
        listadiscapacidad='NO HAY REGISTROS'
    try:
        if profesor.persona.emailinst:
            if clase:
                aula =  clase.aula


            email.attach(MIMEText('<h3><b> Docente : </b>'+ str(elimina_tildes(profesor.persona.nombre_completo())) +'<br/>' +
                                  '<b> Correo:</b>'+ str(elimina_tildes(profesor.persona.emailinst)) + '<br/>'+
                                  '<b> Asignatura : </b>'+str(elimina_tildes( profesormateria.materia.asignatura.nombre))+'<br/>'
                                  '<b> Nivel : </b>' + str(elimina_tildes(profesormateria.materia.nivel.nivelmalla.nombre)) +'<br/>'+
                                  '<b> Carrera : </b>'+ str(elimina_tildes(profesormateria.materia.nivel.carrera.nombre)) + '<br/>'+
                                  '<b> Paralelo : </b>' + str(elimina_tildes(profesormateria.materia.nivel.paralelo))+ '<br/>'+
                                  '<b> Periodo : </b> ' + str(elimina_tildes(profesormateria.materia.nivel.periodo.nombre))+ '<br/>'
                                  '<b> Desde : </b>' + str(profesormateria.desde) +'<br/>' +
                                  '<b> Hasta : </b>' + str(profesormateria.hasta) + '<br/>'
                                  '<b> Aula : </b>'+ str(elimina_tildes(aula))  + '<br/><br/>'
                                  '<b> Observación : </b>'+ str(elimina_tildes(observacion))  + '</h3><br/>'+
                                  '<b> Estudiantes con Discapacidad : </b>'+ str(listadiscapacidad)  + '</h3><br/>  '+
                                  '<h4>'+ str('Por favor no responder al remitente.')+'</h4>'
            ,'html'))
        else:

            email.attach(MIMEText('<h3><b> Docente : </b>'+ str(elimina_tildes(profesor.persona.nombre_completo())) +'<br/>' +
                                  '<b> Correo:</b>'+ str(elimina_tildes(profesor.persona.email)) + '<br/>'+
                                  '<b> Asignatura : </b>'+str(elimina_tildes( profesormateria.materia.asignatura.nombre))+'<br/>'
                                  '<b> Nivel : </b>' + str(elimina_tildes(profesormateria.materia.nivel.nivelmalla.nombre)) +'<br/>'+
                                  '<b> Carrera : </b>'+ str(elimina_tildes(profesormateria.materia.nivel.carrera.nombre)) + '<br/>'+
                                  '<b> Paralelo : </b>' + str(elimina_tildes(profesormateria.materia.nivel.paralelo))+ '<br/>'+
                                  '<b> Periodo : </b> ' + str(elimina_tildes(profesormateria.materia.nivel.periodo.nombre))+ '</h3><br/>'
                                  '<b> Desde : </b>' + str(profesormateria.desde) +'<br/>' +
                                  '<b> Hasta : </b>' + str(profesormateria.hasta) + '<br/><br/>'+
                                  '<b> Observación : </b>'+ str(elimina_tildes(observacion))  + '</h3><br/>  <br/>'+
                                  '<b> Estudiantes con Discapacidad : </b>'+ str(listadiscapacidad)  + '</h3><br/>  '+
                                  '<h4>'+ str('Por favor no responder al remitente.')+'</h4>'
            ,'html'))

    except Exception as ex:
         pass
    # email.attach(load_file('C://repoaka//media//reportes_excel//'+nombre ,'listadoalumnos.xls'))
    email.attach(load_file(MEDIA_ROOT +'/reportes_excel/'+nombre ,'listadoalumnos.xls'))
    smtp = smtplib.SMTP(smtp_server)
    smtp.starttls()
    smtp.login(smtp_user,smtp_pass)
    try:
        smtp.sendmail('sgaitb@itb.edu.ec', emaillis.split(","), email.as_string())
    except Exception as ex:
         pass
    smtp.quit()
    print("E-mail enviado!")

def load_file(file, file_name):
    read_file = open(file,'rb')
    attach = MIMEBase('application', "octet-stream")
    attach.set_payload(read_file.read())
    read_file.close()
    encoders.encode_base64(attach)
    attach.add_header('Content-Disposition', 'attachment', filename=file_name)
    return attach


