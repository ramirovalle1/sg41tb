from datetime import datetime, timedelta
import json
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from decorators import secure_module
from settings import VALIDAR_ENTRADA_SISTEMA_CON_DEUDA,  TIPO_OTRO_RUBRO, TIPO_CONGRESO_RUBRO
from sga.commonviews import addUserData,ip_client_address
from sga.models import Inscripcion, GrupoSeminario, Matricula, InscripcionSeminario, Rubro, RubroOtro, TipoOtroRubro, ObservacionInscripcion, InscripcionGrupoPonencia, GrupoPonencia, elimina_tildes, AbreviaturaTitulo, RubroMatricula
from sga.forms import TituloForm, AbreviaturaTituloForm, GrupoPonenciaForm, InscripcionGrupoPonenciaForm
from django.utils.encoding import force_str
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION


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
@secure_module
def view(request):
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action =='consulta':
                try:
                    matricula = Matricula.objects.get(pk=request.POST['matricula'])
                    if (InscripcionSeminario.objects.filter(matricula = matricula,gruposeminario__activo=True).count()  +1)% 4 == 0 and InscripcionSeminario.objects.filter(matricula = matricula,gruposeminario__activo=True).count() > 1:
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as ex:
                    pass

            if action =='consulta_pago':
                try:
                    matricula = Matricula.objects.get(pk=request.POST['matricula'])
                    # if (InscripcionSeminario.objects.filter(matricula = matricula,gruposeminario__activo=True).count()  +1)% 4 == 0 and InscripcionSeminario.objects.filter(matricula = matricula,gruposeminario__activo=True).count() > 1:
                    #     if RubroMatricula.objects.filter(rubro__inscripcion = matricula.inscripcion,rubro__cancelado=True).exists() or not RubroMatricula.objects.filter(rubro__inscripcion = matricula.inscripcion).exists():
                    if not InscripcionSeminario.objects.filter(gruposeminario__id = request.POST['id'],matricula = matricula).exists():
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad2"}),content_type="application/json")
                    # else:
                    #     return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                except Exception as ex:
                    pass

            if action =='consulta_pago_congreso':
                try:
                    matricula = Matricula.objects.get(pk=request.POST['matricula'])
                    if InscripcionSeminario.objects.filter(matricula=matricula,gruposeminario__activo=True).exists():
                        return HttpResponse(json.dumps({"result":"inscrip"}),content_type="application/json")
                    if not ObservacionInscripcion.objects.filter(inscripcion=matricula.inscripcion,tipo__id=3).exists():
                        return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                    else:
                        return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

                except Exception as ex:
                    pass

            if action =='add_titulo':
                try:
                    m = Matricula.objects.get(pk=request.POST['idmatricula'])
                    nombre = elimina_tildes(m.inscripcion.persona.nombre_completo_inverso())
                    if 'abreviatura' in request.POST:
                        titulo = AbreviaturaTitulo.objects.get(pk=request.POST['abreviatura'])
                        titulo = (titulo.abreviatura+' '+nombre).upper()
                    if 'sin_titulo' in request.POST:
                        titulo = nombre
                    if 'otro' in request.POST:
                        tit = ''.join(request.POST['otro'])
                        if '.' in request.POST['otro']:
                            titulo = (request.POST['otro']+' '+nombre).upper()
                        else:
                            titulo = (tit+'.'+' '+nombre).upper()
                    m.inscripcion.titulo_cert = titulo
                    m.inscripcion.save()
                    client_address = ip_client_address(request)
                    LogEntry.objects.log_action(
                        user_id         = request.user.pk,
                        content_type_id = ContentType.objects.get_for_model(m.inscripcion).pk,
                        object_id       = m.inscripcion.id,
                        object_repr     = force_str(m.inscripcion),
                        action_flag     = CHANGE,
                        change_message  =  "Cambiado Titulo a Imprimir  " +  '(' + client_address + ')' )
                    return HttpResponseRedirect('/alu_seminario')
                except Exception as ex:
                    print(ex)
                    return HttpResponseRedirect('/alu_seminario?&error=Ocurrio un error, vuelva a intentarlo.')

            if action == 'add_ponencia':
                try:
                    f = InscripcionGrupoPonenciaForm(request.POST)
                    if f.is_valid():
                        try:
                            if request.POST['ban'] == '1':
                                grupo = GrupoPonencia.objects.filter().order_by('-codigo')[:1].get()
                                num = grupo.codigo[1:]
                                num = int(num)+1
                                ponencia = GrupoPonencia(nombre=f.cleaned_data['nombre'],
                                                         codigo= 'P'+str(num),
                                                         # precio = PRECIO_PONENCIA,
                                                         horainicio = f.cleaned_data['horainicio'],
                                                         horafin = f.cleaned_data['horafin'],
                                                         integrantes = f.cleaned_data['integrantes'],
                                                         tipo = f.cleaned_data['tipo'],
                                                         activo = True)
                                ponencia.save()
                                mensaje = 'Adicionar'
                                inscrip_ponencia = InscripcionGrupoPonencia(grupoponencia=ponencia,
                                                   matricula = Matricula.objects.get(pk=request.POST['matricula']),
                                                   autor = True,
                                                   institucion=request.POST['institucion'],
                                                   usuario=request.user,
                                                   fecha=datetime.now())
                                inscrip_ponencia.save()

                                # if  ObservacionInscripcion.objects.filter(inscripcion=inscripcion.matricula().inscripcion,tipo__id=3).exists():
                                # tipootro = TipoOtroRubro.objects.get(pk=TIPO_CONGRESO_RUBRO)
                                # rubro = Rubro(fecha=datetime.now().date(),
                                #               valor=PRECIO_PONENCIA,
                                #               inscripcion=inscripcion.matricula().inscripcion,
                                #               cancelado=False,
                                #               fechavence=datetime.now())
                                # rubro.save()
                                # rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion='PONENCIA ' + str(ponencia.id) + ' - '+str(ponencia.codigo) )
                                # rubrootro.save()
                                # inscrip_ponencia.rubrootro = rubrootro
                                # inscrip_ponencia.save()

                                # Obtain client ip address
                                # client_address = ip_client_address(request)
                                # # Log de ADICIONAR AUTOR PONENCIA
                                # LogEntry.objects.log_action(
                                #     user_id         = request.user.pk,
                                #     content_type_id = ContentType.objects.get_for_model(ponencia).pk,
                                #     object_id       = inscripcion.id,
                                #     object_repr     = force_str(ponencia),
                                #     action_flag     = ADDITION,
                                #     change_message  = 'Adicionado Autor Ponencia (' + client_address + ')' )

                            else:
                                ponencia = GrupoPonencia.objects.get(pk=int(request.POST['ponencia']))
                                ponencia.nombre=f.cleaned_data['nombre']
                                ponencia.integrantes = f.cleaned_data['integrantes']
                                ponencia.tipo = f.cleaned_data['tipo']
                                ponencia.activo=True
                                ponencia.save()
                                mensaje = 'Editado'

                            # Log Agregar Ponencia
                            client_address = ip_client_address(request)
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(ponencia).pk,
                                object_id       = ponencia.id,
                                object_repr     = force_str(ponencia),
                                action_flag     = ADDITION,
                                change_message  = mensaje + " Ponencia " +  '(' + client_address + ')' )

                            return HttpResponseRedirect("/alu_seminario?ensayo="+request.POST['matricula'])
                        except Exception as ex:
                            print(ex)
                            return HttpResponseRedirect("alu_seminario?ensayo="+request.POST['matricula']+"&action=add_ponencia&error=1",)

                    else:
                        return HttpResponseRedirect("/alu_seminario?ensayo="+request.POST['matricula']+"&error=1")
                except Exception as ex:
                    return HttpResponseRedirect("/alu_seminario?ensayo="+request.POST['matricula']+"&error=Error al ingresar aporte cientifico, vuelva a intentarlo")

    else:
        data = {'title': ' Talleres'}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'matricularse':
                try:
                    matricula = Matricula.objects.get(pk=request.GET['matricula'])
                    seminario = GrupoSeminario.objects.get(pk=request.GET['id'])
                    if seminario.inscritos() < seminario.capacidad:
                        if not InscripcionSeminario.objects.filter(gruposeminario=seminario,matricula = matricula,gruposeminario__activo=True).exists():
                            iseminario = InscripcionSeminario(gruposeminario=seminario,
                                                              matricula = matricula,
                                                              fecha=datetime.now().date())
                            iseminario.save()
                            hoy =datetime.now().date() + timedelta(2)
                            if not  seminario.libre:
                                if InscripcionSeminario.objects.filter(matricula = matricula, gruposeminario__activo=True, gruposeminario__libre=False).count()>1:
                                # if  ObservacionInscripcion.objects.filter(inscripcion=matricula.inscripcion,tipo__id=3).exists():
                                # if InscripcionSeminario.objects.filter(matricula = matricula).count() % 4 != 0 and InscripcionSeminario.objects.filter(matricula = matricula).count() >= 1:
                                    tipootro = TipoOtroRubro.objects.get(pk=TIPO_OTRO_RUBRO)
                                    rubro = Rubro(fecha=datetime.now().date(),
                                                  valor=seminario.precio,
                                                  inscripcion=matricula.inscripcion,
                                                  cancelado=False,
                                                  fechavence=hoy)
                                    rubro.save()
                                    rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion='TALLER ' + str(seminario.id) + ' - '+str(seminario.carrera.alias) )

                                    rubrootro.save()
                                    iseminario.rubrootro = rubrootro
                                    iseminario.save()
                            client_address = ip_client_address(request)

                            # Log de EDITAR HORARIO CLASE
                            LogEntry.objects.log_action(
                                user_id         = request.user.pk,
                                content_type_id = ContentType.objects.get_for_model(iseminario).pk,
                                object_id       = iseminario.id,
                                object_repr     = force_str(iseminario),
                                action_flag     = ADDITION,
                                change_message  = 'Adicionada Inscripcion Taller (' + client_address + ')'  )
                except Exception as ex:
                    pass

            elif action == 'add_ponencia':
                data['form'] = InscripcionGrupoPonenciaForm(initial={"fecha":datetime.now().date()})
                data['ban'] =1
                data['matricula'] = request.GET['ensayo']
                if 'error' in request.GET:
                        data['error'] = request.GET['error']
                return render(request ,"alu_seminario/add_ponencia.html" ,  data)

            elif action == 'editar':
                ponencia = GrupoPonencia.objects.get(pk=request.GET['id'])
                initial = model_to_dict(ponencia)
                data['form'] = InscripcionGrupoPonenciaForm(initial=initial)
                if 'error' in request.GET:
                    data['error'] = 1
                data['ban'] = 2
                data['ponencia'] =ponencia
                return render(request ,"alu_seminario/add_ponencia.html" ,  data)

            return  HttpResponseRedirect('/alu_seminario')

        else:
            try:
                    inscripcion = Inscripcion.objects.get(persona=data['persona'])

                    #Comprobar que no tenga deudas para que no pueda usar el sistema
                    if VALIDAR_ENTRADA_SISTEMA_CON_DEUDA and inscripcion.tiene_deuda():
                        return HttpResponseRedirect("/")

                    #Comprobar que el alumno este matriculado
                    if not inscripcion.matriculado():
                        if not inscripcion.matricula_set.exists():
                            return HttpResponseRedirect("/?info=Ud. aun no ha sido matriculado")
                    if inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False).exists():
                        matricula = inscripcion.matricula_set.filter(nivel__periodo__activo=True, nivel__cerrado=False)[:1].get()
                    else:
                        matricula = inscripcion.matricula_set.filter().order_by('-id')[:1].get()

                    search = ""
                    if 's' in request.GET:
                        search = request.GET['s']
                    # talleres = GrupoSeminario.objects.filter(activo=True, empezardesde__lte=datetime.now().date(),carrera=matricula.inscripcion.carrera).order_by('id')
                    talleres = GrupoSeminario.objects.filter(activo=True, empezardesde__lte=datetime.now().date()).order_by('-id')
                    if 'taller' in request.GET:
                        i = InscripcionSeminario.objects.filter(matricula = matricula,gruposeminario__activo=True).values('gruposeminario__id')
                        talleres = talleres.filter(id__in=i).order_by('id')
                        data['taller'] = 1

                    elif 'ensayo' in request.GET:
                        ins = InscripcionGrupoPonencia.objects.filter(matricula=matricula, activo=True, grupoponencia__activo=True).values('grupoponencia')
                        ponencia = GrupoPonencia.objects.filter(id__in=ins)
                        data['ponencias'] = ponencia
                        data['ponencia'] = 2

                    if search:
                        # talleres = GrupoSeminario.objects.filter(Q(activo=True,inicio__gte=datetime.now().date(),expositor__icontains=search,empezardesde__lte=datetime.now().date())|Q(inicio__gte=datetime.now().date(),taller__icontains=search,empezardesde__lte=datetime.now().date(),carrera=matricula.inscripcion.carrera)|Q(inicio__gte=datetime.now().date(),id__icontains=search,empezardesde__lte=datetime.now().date(),carrera=matricula.inscripcion.carrera)).order_by('id')
                        # talleres = GrupoSeminario.objects.filter(Q(activo=True,inicio__gte=datetime.now().date(),expositor__icontains=search,empezardesde__lte=datetime.now().date())|Q(inicio__gte=datetime.now().date(),taller__icontains=search,empezardesde__lte=datetime.now().date())|Q(inicio__gte=datetime.now().date(),id__icontains=search,empezardesde__lte=datetime.now().date())).order_by('id')
                        # talleres = GrupoSeminario.objects.filter(Q(inicio__gte=datetime.now().date(),expositor__icontains=search,empezardesde__lte=datetime.now().date(),carrera=matricula.inscripcion.carrera)|Q(inicio__gte=datetime.now().date(),taller__icontains=search,empezardesde__lte=datetime.now().date(),carrera=matricula.inscripcion.carrera)|Q(inicio__gte=datetime.now().date(),id__icontains=search,empezardesde__lte=datetime.now().date(),carrera=matricula.inscripcion.carrera)).order_by('id')
                        talleres = talleres.filter(Q(expositor__icontains=search)|Q(taller__icontains=search,empezardesde__lte=datetime.now().date())|Q(id__icontains=search))

                    data['matricula'] = matricula
                    paging = MiPaginador(talleres, 30)
                    p = 1
                    try:
                        if 'page' in request.GET:
                            p = int(request.GET['page'])
                            paging = MiPaginador(talleres, 30)
                        page = paging.page(p)
                    except Exception as ex:
                        page = paging.page(1)

                    data['paging'] = paging
                    data['form'] = AbreviaturaTituloForm()
                    data['rangospaging'] = paging.rangos_paginado(p)
                    data['page'] = page
                    data['talleres'] = page.object_list
                    data['inscripcion'] = inscripcion
                    if InscripcionSeminario.objects.filter(matricula__inscripcion=inscripcion, gruposeminario__activo=True).exists():
                        data['inscripcion_taller'] = InscripcionSeminario.objects.filter(matricula__inscripcion=inscripcion, gruposeminario__activo=True)[:1].get()
                    data['tienetaller'] = InscripcionSeminario.objects.filter(matricula = matricula,gruposeminario__activo=True).exists()

                    # data['esta_matriculado'] = Nivel.objects.filter(carrera=matricula.inscripcion.carrera, cerrado=False).exists()
                    data['esta_matriculado'] = GrupoSeminario.objects.filter(activo=True, empezardesde__lte=datetime.now().date(),carrera=matricula.inscripcion.carrera).exists()
                    data['tieneensayo'] = InscripcionGrupoPonencia.objects.filter(matricula=matricula, activo=True, grupoponencia__activo=True).exists()
                    data['hoy'] = datetime.today()
                    data['search'] = search if search else ""

                    if inscripcion.titulo_cert :
                        cadena = inscripcion .titulo_cert
                        d = list(cadena)
                        nueva = []
                        for c in d:
                            nueva.append(c)
                            if c != '.':
                                pass
                            else:
                                break
                        if inscripcion.titulo_cert != inscripcion.persona.nombre_completo_inverso():
                            data['titulo_cert']= "".join(nueva).upper()
                        else:
                            data['titulo_cert']=''
                    else:
                        data['titulo_cert']=''
                    data['tiene_titulo_cert']= inscripcion.titulo_cert if inscripcion.titulo_cert else ''
                    rubro = RubroMatricula.objects.filter(matricula=matricula, rubro__cancelado=True).exists()
                    data['matri_pagada'] = rubro

                    return render(request ,"alu_seminario/seminario.html" ,  data)
            except Exception as ex:
                print(ex)
                return HttpResponseRedirect("/")