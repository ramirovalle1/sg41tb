from datetime import datetime
from django.contrib.admin.models import LogEntry, DELETION, CHANGE, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_str
from bib.forms import DocumentoForm, PrestamoDocumentoForm, AutoresTesisForm, PlagioForm
from bib.models import Documento, TipoDocumento, PrestamoDocumento, AutoresTesis
from sga.commonviews import addUserData, ip_client_address
from sga.inscripciones import MiPaginador
from sga.models import Persona,Inscripcion,HistoricoRecordAcademico, Asignatura, AsignaturaMalla, RecordAcademico, Profesor, Carrera
from settings import ANIO_TESIS,TIPO_DOCUMENTO


@login_required(redirect_field_name='ret', login_url='/login')
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            f = DocumentoForm(request.POST, request.FILES)
            try:
                if f.is_valid():
                    if not Documento.objects.filter(codigo=f.cleaned_data['codigo']).exists():
                        documento = Documento(codigo=f.cleaned_data['codigo'], nombre=f.cleaned_data['nombre'],
                                            autor=f.cleaned_data['autor'], tipo=f.cleaned_data['tipo'],
                                            anno=f.cleaned_data['anno'], emision=f.cleaned_data['emision'],
                                            palabrasclaves=f.cleaned_data['palabrasclaves'],
                                            fisico=f.cleaned_data['fisico'],
                                            copias=f.cleaned_data['copias'],
                                            paginas=f.cleaned_data['paginas'],
                                            editora=f.cleaned_data['editora'],
                                            sede=f.cleaned_data['sede'],
                                            codigodewey=f.cleaned_data['codigodewey'],
                                            idioma=f.cleaned_data['idioma'],
                                            tutor=f.cleaned_data['tutor'],
                                            resumen=f.cleaned_data['resumen'])

                        if 'digital' in request.FILES:
                            documento.digital=request.FILES['digital']
                        if 'portada' in request.FILES:
                            documento.portada=request.FILES['portada']

                        documento.save()
                        # OCU 13-marzo-2018 incluir estudiante y docente tutor en las tesis
                        if request.POST['autor1_id']:
                            inscripcion=Inscripcion.objects.get(pk=request.POST['autor1_id'])
                            documento.inscripcion=inscripcion

                        if request.POST['tutor1_id']:
                            docente=Profesor.objects.get(pk=request.POST['tutor1_id'])
                            documento.docente=docente
                        documento.save()

                        #OCU 14 diciembre 2018 incluir carrera
                        if request.POST['carrera_id']:
                            carrera=Carrera.objects.get(pk=request.POST['carrera_id'])
                            documento.carrera=carrera
                        documento.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de ADICIONAR DOCUMENTO DE LA BIBLIOTECA
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(documento).pk,
                            object_id       = documento.id,
                            object_repr     = force_str(documento),
                            action_flag     = ADDITION,
                            change_message  = 'Adicionado Documento en Biblioteca (' + client_address + ')' )
                    else:
                        return HttpResponseRedirect("/documentos?action=add&error=1")
            except:
                return HttpResponseRedirect("/documentos?action=add&e_add=3")

            else:
                return HttpResponseRedirect("/documentos?action=add")

        elif action=='edit':
            documento = Documento.objects.get(pk=request.POST['id'])
            f = DocumentoForm(request.POST, request.FILES)
            try:
                if f.is_valid():
                    codigo=f.cleaned_data['codigo']
                    if not Documento.objects.filter(codigo=codigo).exclude(id=documento.id).exists():
                        documento.codigo=f.cleaned_data['codigo']
                        documento.nombre=f.cleaned_data['nombre']
                        if f.cleaned_data['autor']:
                            autor=f.cleaned_data['autor']
                        else:
                            autor=documento.autor
                        documento.autor=autor
                        documento.tipo=f.cleaned_data['tipo']
                        documento.anno=f.cleaned_data['anno']
                        documento.emision=f.cleaned_data['emision']
                        documento.palabrasclaves=f.cleaned_data['palabrasclaves']
                        documento.editora=f.cleaned_data['editora']
                        documento.sede=f.cleaned_data['sede']
                        documento.codigodewey=f.cleaned_data['codigodewey']
                        documento.idioma=f.cleaned_data['idioma']

                        documento.fisico=f.cleaned_data['fisico']
                        documento.copias=f.cleaned_data['copias']
                        documento.paginas=f.cleaned_data['paginas']
                        if f.cleaned_data['tutor']:
                            tutor=f.cleaned_data['tutor']
                        else:
                            tutor=documento.tutor
                        documento.tutor=tutor

                        documento.resumen=f.cleaned_data['resumen']

                        if 'digital' in request.FILES:
                            documento.digital=request.FILES['digital']

                        if 'portada' in request.FILES:
                            documento.portada=request.FILES['portada']

                        documento.save()

                        # OCU 13-marzo-2018 incluir estudiante y docente tutor en las tesis
                        if 'autor1_id' in request.POST:
                            if request.POST['autor1_id']:
                                inscripcion=Inscripcion.objects.get(pk=request.POST['autor1_id'])
                                documento.inscripcion=inscripcion
                                documento.save()

                        if 'tutor1_id' in request.POST:
                            if request.POST['tutor1_id']:
                                docente=Profesor.objects.get(pk=request.POST['tutor1_id'])
                                documento.docente=docente
                                documento.save()

                        # OCU 14 diciembre 2018 incluir carrera
                        if 'carrera_id' in request.POST:
                            if request.POST['carrera_id']:
                                carrera=Carrera.objects.get(pk=request.POST['carrera_id'])
                                documento.carrera=carrera
                                documento.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de EDITAR DOCUMENTO DE LA BIBLIOTECA
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(documento).pk,
                            object_id       = documento.id,
                            object_repr     = force_str(documento),
                            action_flag     = CHANGE,
                            change_message  = 'Modificado Documento de Biblioteca (' + client_address + ')' )
                        return HttpResponseRedirect("/documentos?c="+str(documento.id))
                    else:
                        return HttpResponseRedirect("/documentos?action=edit&id="+str(documento.id)+"&error=2")

                else:
                    return HttpResponseRedirect("/documentos?action=edit&id="+str(documento.id))
            except:
                return HttpResponseRedirect("/documentos?action=edit&id="+str(documento.id)+"&e_edit=3")

        elif action=='delete':
            documento = Documento.objects.get(pk=request.POST['id'])

            #Obtain client ip address
            client_address = ip_client_address(request)

            # Log de BORRAR DOCUMENTO DE LA BIBLIOTECA
            LogEntry.objects.log_action(
                user_id         = request.user.pk,
                content_type_id = ContentType.objects.get_for_model(documento).pk,
                object_id       = documento.id,
                object_repr     = force_str(documento),
                action_flag     = DELETION,
                change_message  = 'Eliminado Documento de Biblioteca (' + client_address + ')')

            documento.delete()

        elif action=='addprestamo':
            try:
                documento = Documento.objects.get(pk=request.POST['id'])
                responsableentrega= request.session['persona']
                persona = Persona.objects.filter(pk=request.POST['persona_id'])[:1].get()
                # OCU 20-sep-2017 validar si es alumno y esta matriculado
                matriculado = False
                if Inscripcion.objects.filter(persona=request.POST['persona_id']).exists()   :
                    inscripcion = Inscripcion.objects.filter(persona=request.POST['persona_id'])[:1].get()
                    # OCU 19-oct-2017 si estudiante esta egresado si se le puede realizar el prestamo
                    if  not inscripcion.matriculado() and not inscripcion.alumno_estado() :
                        return HttpResponseRedirect("/documentos?action=addprestamo&id="+str(documento.id)+"&error=1")
                    matriculado = True
                # else:
                # if persona.profesor() and persona.activo()or matriculado or persona.administrativos():
                if persona.profesor() and persona.activo()or matriculado or persona.administrativos():
                    f = PrestamoDocumentoForm(request.POST)
                    if f.is_valid():
                        prestamo = PrestamoDocumento(documento=documento,persona=persona,
                                                    responsableentrega=responsableentrega, tiempo=f.cleaned_data['tiempo'],
                                                    fechaentrega=datetime.today(), horaentrega=datetime.now().time(),
                                                    entregado=f.cleaned_data['entregado'], recibido = False)
                        prestamo.save()

                        #Obtain client ip address
                        client_address = ip_client_address(request)

                        # Log de PRESTAMO DOCUMENTO DE LA BIBLIOTECA
                        LogEntry.objects.log_action(
                            user_id         = request.user.pk,
                            content_type_id = ContentType.objects.get_for_model(prestamo).pk,
                            object_id       = prestamo.id,
                            object_repr     = force_str(prestamo),
                            action_flag     = ADDITION,
                            change_message  = 'Prestamo de Documento en Biblioteca (' + client_address + ')' )

                        return HttpResponseRedirect("/prestamos")
                return HttpResponseRedirect("/documentos?action=addprestamo&id="+str(documento.id)+"&error=2")
            except Exception as e:
                return HttpResponseRedirect("/?info="+str(e))


        elif action=='addautores':
            documento = Documento.objects.get(pk=request.POST['id'])
            inscripcion=Inscripcion.objects.get(pk=request.POST['autor1_id'])
            f = AutoresTesisForm(request.POST)
            if f.is_valid():
                autores = AutoresTesis(documento=documento,
                                       estudiante_id = f.cleaned_data['autor1_id'],
                                       nota=f.cleaned_data['nota'],
                                       plagio=f.cleaned_data['plagio'],
                                       fechasustentacion=f.cleaned_data['fechasustentacion'],
                                       observaciones=f.cleaned_data['observaciones'],
                                       usuario=request.user,
                                       fecha=datetime.now())
                autores.save()

                client_address = ip_client_address(request)
                # Log de Ingreso Autores Tesis
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(documento).pk,
                    object_id       = documento.id,
                    object_repr     = force_str(documento),
                    action_flag     = ADDITION,
                    change_message  = 'Agregado autores Tesis (' + client_address + ')' )

                if not HistoricoRecordAcademico.objects.filter(inscripcion=inscripcion, asignatura__in= Asignatura.objects.filter(nombre__icontains='TRABAJO')).exists():
                    inscripcionmalla = inscripcion.malla_inscripcion()
                    malla = inscripcionmalla.malla
                    asignaturasmalla = AsignaturaMalla.objects.filter(malla=malla,asignatura__nombre__icontains='TRABAJO').get()

                    try:
                        historico = HistoricoRecordAcademico(inscripcion=inscripcion,
                                                             asignatura=asignaturasmalla.asignatura,
                                                             nota=f.cleaned_data['nota'],
                                                             asistencia=100,fecha=datetime.now().date(),
                                                             aprobada=True,convalidacion=False,pendiente=False)

                        historico.save()
                    except Exception as e:
                        pass
                    record = RecordAcademico(inscripcion=inscripcion, asignatura=asignaturasmalla.asignatura,
                                             nota=f.cleaned_data['nota'], asistencia=100,
                                             fecha=datetime.now().date(), aprobada=True,
                                             convalidacion=False, pendiente=False)
                    record.save()

                    # Obtain client ip address
                    client_address = ip_client_address(request)
                    # Log de ADICIONAR NOTA TESIS AUTOR
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(inscripcion).pk,
                        object_id       = inscripcion.id,
                        object_repr     = force_str(record),
                        action_flag     = ADDITION,
                        change_message  = 'Adicionado Nota Tesis Estudiante Autor1 (' + client_address + ')' )

                return HttpResponseRedirect("/documentos?c="+str(documento.id))

            return HttpResponseRedirect("/documentos?action=addautores&id="+str(documento.id)+"&error=1")

        elif action=='addplagio':
            documento = Documento.objects.get(pk=request.POST['id'])
            inscripcion=Inscripcion.objects.get(pk=request.POST['autor1_id'])
            f = PlagioForm(request.POST)
            if f.is_valid():
                autores = AutoresTesis(documento=documento,
                                       estudiante_id = f.cleaned_data['autor1_id'],
                                       plagio=f.cleaned_data['plagio'],
                                       usuario=request.user,
                                       fecha=datetime.now())
                autores.save()

                client_address = ip_client_address(request)
                # Log de Ingreso Autores Tesis
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(documento).pk,
                    object_id       = documento.id,
                    object_repr     = force_str(documento),
                    action_flag     = ADDITION,
                    change_message  = 'Agregado Plagio Tesis (' + client_address + ')' )

                return HttpResponseRedirect("/documentos?c="+str(documento.id))

        return HttpResponseRedirect("/documentos")

    else:
        data = {'title': 'Gestion de Biblioteca'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Adicionar Documento a la Biblioteca'
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                if 'e_add' in request.GET:
                    data['e_add'] = request.GET['e_add']
                data['form'] = DocumentoForm()
                data['tipodoc']=TIPO_DOCUMENTO
                return render(request ,"biblioteca/add.html" ,  data)

            elif action=='edit':
                data['title'] = 'Editar Documento de la Biblioteca'
                documento = Documento.objects.get(pk=request.GET['id'])
                if 'error' in request.GET:
                    data['error'] = request.GET['error']
                if 'e_edit' in request.GET:
                    data['e_edit'] = request.GET['e_edit']
                initial = model_to_dict(documento)
                data['form'] = DocumentoForm(initial=initial)
                data['documento'] = documento
                data['tipodoc']=TIPO_DOCUMENTO
                return render(request ,"biblioteca/edit.html" ,  data)

            elif action=='delete':
                data['title'] = 'Eliminar Documento de la Biblioteca'
                data['documento'] = Documento.objects.get(pk=request.GET['id'])
                return render(request ,"biblioteca/delete.html" ,  data)

            elif action=='addprestamo':
                if 'error' in request.GET:
                    if request.GET['error'] == '1':
                        data['error'] = '1'
                    else:
                        data['error'] = '2'

                data['title'] = 'Prestamos de Documentos'
                documento = Documento.objects.get(pk=request.GET['id'])
                data['form'] = PrestamoDocumentoForm(initial={'tiempo': 24 })
                data['documento'] = documento
                return render(request ,"biblioteca/addprestamo.html" ,  data)

            elif action=='addautores':
                data['title'] = 'Autores de Tesis y Calificacion'
                data['documento']  = Documento.objects.get(pk=request.GET['id'])
                docuform = AutoresTesisForm(initial={'fechasustentacion': datetime.now().strftime("%d-%m-%Y")})
                data['form'] = docuform

                if 'error' in request.GET:
                    data['error'] = 1

                return render(request ,"biblioteca/addautores.html" ,  data)

            elif action=='addplagio':
                data['title'] = 'Agregar Plagio'
                data['documento']  = Documento.objects.get(pk=request.GET['id'])
                docuform = PlagioForm()
                data['form'] = docuform

                if 'error' in request.GET:
                    data['error'] = 1

                return render(request ,"biblioteca/addplagio.html" ,  data)

            elif action=='verautores':
                data['title'] = 'Autores de Tesis y Calificacion'
                documento = Documento.objects.get(pk=request.GET['id'])
                autores  = AutoresTesis.objects.get(documento=request.GET['id'])
                data['form'] = autores
                data['documento']=documento
                docuform = AutoresTesisForm(initial={'autor1': autores.estudiante.persona.nombre_completo(),'nota':autores.nota,'plagio':autores.plagio,'observaciones':autores.observaciones,'fechasustentacion':autores.fechasustentacion})
                data['form'] = docuform
                return render(request ,"biblioteca/verautores.html" ,  data)

        else:
            search = None

            if 's' in request.GET:
                search = request.GET['s']
            if search:
                tutor =[]
                if search:
                    ss = search.split(' ')
                    while '' in ss:
                        ss.remove('')
                    if len(ss)==1:
                        tutor = Documento.objects.filter(Q(docente__persona__apellido1__icontains=search)|Q(docente__persona__apellido2__icontains=search)|Q(inscripcion__persona__apellido1__icontains=search)|Q(inscripcion__persona__apellido2__icontains=search) |Q(inscripcion__persona__cedula__icontains=search) |Q(tutor__icontains=search) |Q(autor__icontains=search) 	).values('id')
                        # autor = Documento.objects.filter(Q(inscripcion__persona__apellido1__icontains=search)|Q(inscripcion__persona__apellido2__icontains=search)).values('id')

                    else:
                        tutor = Documento.objects.filter(Q(docente__persona__apellido1__icontains=ss[0])|Q(docente__persona__apellido2__icontains=ss[1])|Q(inscripcion__persona__apellido1__icontains=ss[0])|Q(inscripcion__persona__apellido2__icontains=ss[1]) |Q(tutor__icontains=search) |Q(autor__icontains=search)).values('id')
                        # autor = Documento.objects.filter(Q(inscripcion__persona__apellido1__icontains=ss[0])|Q(inscripcion__persona__apellido1__icontains=ss[1])).values('id')

                documentos = Documento.objects.filter(Q (id__in=tutor)| Q(codigo__icontains=search) | Q(nombre__icontains=search) | Q(autor__icontains=search)  | Q(tutor__icontains=search) | Q(anno__icontains=search) ).order_by('-anno')
            else:
                documentos = Documento.objects.all().order_by('-anno')

            if 't' in request.GET:
                t = request.GET['t']
                documentos = documentos.filter(tipo__id=t)
                data['tipo'] = int(t)

            if 'c' in request.GET:
                c = request.GET['c']
                documentos = Documento.objects.filter(pk=c)

            paging = MiPaginador(documentos, 50)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(p)

            data['paging'] = paging
            data['rangospaging'] = paging.rangos_paginado(p)
            data['page'] = page
            data['search'] = search if search else ""
            data['documentos'] = page.object_list
            data['tipos'] = TipoDocumento.objects.all()
            data['tipodoc']=TIPO_DOCUMENTO

            return render(request ,"biblioteca/documentos.html" ,  data)
