from datetime import datetime, timedelta
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str
from decorators import secure_module
from settings import VALIDAR_ENTRADA_SISTEMA_CON_DEUDA, ARCHIVO_TIPO_PLANCLASE
from sga.commonviews import addUserData
from sga.forms import DeberAlumnoForm
from sga.models import Matricula, RecordAcademico, Inscripcion, Periodo, LeccionGrupo, Profesor, Materia, DeberAlumno


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
         action = request.POST['action']
         if action == 'adddeberes':
            leccion = LeccionGrupo.objects.get(pk=request.POST['leccion'])
            inscripcion = Inscripcion.objects.get(persona=request.session['persona'])
            deberalumno = DeberAlumno(lecciongrupo=leccion,
                                      inscripcion=inscripcion,
                                      fechaentrega = datetime.today().date(),
                                      archivo = request.FILES['archivo'])
            deberalumno.save()
            try:
            # case server externo
                 client_address = request.META['HTTP_X_FORWARDED_FOR']
            except:
            # case localhost o 127.0.0.1
                    client_address = request.META['REMOTE_ADDR']
                # Log de CERRAR MATERIA
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(deberalumno).pk,
                object_id       = deberalumno.id,
                object_repr     = force_str(deberalumno),
                action_flag     = ADDITION,
                change_message  = 'Adicionado Deber  (' + client_address + ')' )
            return HttpResponseRedirect("/alu_documentos")

         elif action =='actualizar':
            deber = DeberAlumno.objects.get(pk=request.POST['leccion'])
            deber.fechaentrega = datetime.today().date()
            deber.archivo = request.FILES['archivo']
            deber.save()

            try:
            # case server externo
                 client_address = request.META['HTTP_X_FORWARDED_FOR']
            except:
            # case localhost o 127.0.0.1
                client_address = request.META['REMOTE_ADDR']
                # Log de CERRAR MATERIA
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(deber).pk,
                object_id       = deber.id,
                object_repr     = force_str(deber),
                action_flag     = ADDITION,
                change_message  = 'Actualizado Deber  (' + client_address + ')' )

            return HttpResponseRedirect("/alu_documentos")


    else:
        data = {'title': ' Ficheros del Alumno'}
        addUserData(request, data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']
                if action=='deberes':
                    data['title'] = 'Deberes por Clases'
                    materia = Materia.objects.get(pk=request.GET['id'])
                    profesor = Profesor.objects.get(pk=request.GET['p'])
                    data['inscripcion'] = Inscripcion.objects.get(persona=request.session['persona'])
                    #leccionesGrupo = LeccionGrupo.objects.filter(materia=materia,profesor=profesor).order_by('-fecha','-horaentrada')
                    leccionesGrupo = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,materia=materia,profesor=profesor).order_by('-fecha', '-horaentrada')

                    paging = Paginator(leccionesGrupo, 40)
                    p=1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)

                    data['paging'] = paging
                    data['page'] = page
                    data['leccionesgrupo'] = page.object_list
                    data['materia'] = materia
                    data['profesor'] = profesor
                    data['hoy'] = datetime.today().date()
                    return render(request ,"alu_documentos/deberesbs.html" ,  data)
                elif action=='material':
                    data['title'] = 'Material de Apoyo por Clases'
                    materia = Materia.objects.get(pk=request.GET['id'])
                    profesor = Profesor.objects.get(pk=request.GET['p'])
                    data['inscripcion'] = Inscripcion.objects.get(persona=request.session['persona'])
                    #leccionesGrupo = LeccionGrupo.objects.filter(materia=materia,profesor=profesor).order_by('-fecha','-horaentrada')
                    leccionesGrupo = LeccionGrupo.objects.filter(materia__nivel__periodo__activo=True,materia=materia,profesor=profesor).order_by('-fecha', '-horaentrada')

                    paging = Paginator(leccionesGrupo, 40)
                    p=1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                        page = paging.page(p)
                    except:
                        page = paging.page(1)

                    data['paging'] = paging
                    data['page'] = page
                    data['leccionesgrupo'] = page.object_list
                    data['materia'] = materia
                    data['profesor'] = profesor
                    data['hoy'] = datetime.today().date()
                    return render(request ,"alu_documentos/material.html" ,  data)

                elif action == 'subir':
                    data['leccion'] = LeccionGrupo.objects.get(pk=request.GET['leccion'])
                    data['form'] = DeberAlumnoForm()
                    return render(request ,"alu_documentos/adddeberesbs.html" ,  data)

                elif action == 'actualizar':
                    data['deber'] = DeberAlumno.objects.filter(lecciongrupo__id=request.GET['id'],inscripcion__id=request.GET['insc'])[:1].get()
                    data['form'] = DeberAlumnoForm()

                    return render(request ,"alu_documentos/actualizadeber.html" ,  data)
                return HttpResponseRedirect("/alu_documentos")
            else:
                try:
                    inscripcion = Inscripcion.objects.get(persona=data['persona'])

                    #Comprobar que no tenga deudas para que no pueda usar el sistema
                    if VALIDAR_ENTRADA_SISTEMA_CON_DEUDA and inscripcion.tiene_deuda():
                        return HttpResponseRedirect("/")

                    #Comprobar que el alumno este matriculado
                    if not inscripcion.matriculado():
                        return HttpResponseRedirect("/?info=Ud. aun no ha sido matriculado")
                    matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False,liberada=False)[:1].get()
                    materiasAsignadas = matricula.materiaasignada_set.all()

                    data['matricula'] = matricula
                    data['materiasasignadas'] = materiasAsignadas
                    data['ARCHIVO_TIPO_PLANCLASE'] = ARCHIVO_TIPO_PLANCLASE

                    return render(request ,"alu_documentos/ficherosbs.html" ,  data)
                except Exception as ex:
                    return HttpResponseRedirect("/")
        except Exception as ex:
            return HttpResponseRedirect("/")