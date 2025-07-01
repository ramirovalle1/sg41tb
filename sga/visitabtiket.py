from datetime import datetime
import json
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from decorators import secure_module
import psycopg2
from django.db.models.query_utils import Q
from settings import TIPO_OTRO_RUBRO, PROFESORES_GROUP_ID, ALUMNOS_GROUP_ID,SISTEMAS_GROUP_ID, CONSUMIDOR_FINAL
from sga.commonviews import addUserData, ip_client_address
from sga.models import NewsTiket, TipoVisitasBox,VisitaTiket,VisTiketDet, Aula, TipoAtencionBox,VisitaBox,TipoOtroRubro,RubroOtro,Rubro, PersonalConvenio, \
     PrecioConsulta, Persona,Inscripcion,RetiradoMatricula,Matricula, BoxEterno,CitasCancelasBox


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
@transaction.atomic()
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'print':
           id=request.POST['idvisita']
           cedula=request.POST['ced']
           precio = None
           tipoatencionbox=None
           horacita=None
           sede=None
           try:
                   if TipoVisitasBox.objects.filter(pk=id)[:1].get().cita:
                        if not PersonalConvenio.objects.filter(identificacion=cedula).exists():
                            return HttpResponse(json.dumps({"result":"badcita","msj":'Debe sacar cita via pagina Web'}),content_type="application/json")
                   if PersonalConvenio.objects.filter(identificacion=cedula).exists():
                       persona = PersonalConvenio.objects.filter(identificacion=cedula)[:1].get()
                       client_address = ip_client_address(request)
                       if Aula.objects.filter(ip=str(client_address),activa=False).exists():
                            sede = Aula.objects.filter(ip=str(client_address),activa=False)[:1].get().sede.id
                       if persona.conveniobox.cita:
                           if BoxEterno.objects.filter(persona_convenio=persona,fechacita=datetime.now().date(),activa=True,check_in=False).exists():
                               boxexterno=BoxEterno.objects.filter(persona_convenio=persona,fechacita=datetime.now().date(),activa=True,check_in=False)[:1].get()
                               if BoxEterno.objects.filter(persona_convenio=persona,fechacita=datetime.now().date(),activa=True,check_in=False,campus=sede).exists():
                                   if boxexterno.en_hora() == 'VENCIDO':
                                       return HttpResponse(json.dumps({"result":"badcita","msj":'Ha expirado la hora de su cita'}),content_type="application/json")
                                   # boxexterno=BoxEterno.objects.filter(persona_convenio=persona,fechacita=datetime.now().date(),activa=True,check_in=False,campus=sede)[:1].get()
                                   boxexterno.check_in = True
                                   boxexterno.fecha_check = datetime.now()
                                   horacita = str(boxexterno.persona_convenio.nombres) + "Hora Cita: " + str(boxexterno.iniciocita)
                                   boxexterno.save()
                               else:
                                   horacita = 'Su cita esta registrada en ' + str(boxexterno.campus.nombre)
                           elif  BoxEterno.objects.filter(persona_convenio=persona,fechacita=datetime.now().date(),activa=True,check_in=True,campus=sede).exists():
                               return HttpResponse(json.dumps({"result":"badcita","msj":'Su cita ya fue registrada'}),content_type="application/json")
                           else:
                               # horacita =
                               return HttpResponse(json.dumps({"result":"badcita","msj":'Debe sacar cita via pagina Web'}),content_type="application/json")

                       if PrecioConsulta.objects.filter(convenio=persona.conveniobox,tipovisita=id).exists():
                           precio = PrecioConsulta.objects.filter(convenio=persona.conveniobox,tipovisita=id)[:1].get()
                   else:
                       gruposexcluidos = [PROFESORES_GROUP_ID,ALUMNOS_GROUP_ID]
                       if Persona.objects.filter(cedula=cedula,usuario__groups__id=PROFESORES_GROUP_ID).exists():
                           persona = Persona.objects.filter(cedula=cedula,usuario__groups__id=PROFESORES_GROUP_ID)[:1].get()
                           if PrecioConsulta.objects.filter(tipovisita=id,tipopersona=4).exists():
                                precio = PrecioConsulta.objects.filter(tipovisita=id,tipopersona=4)[:1].get()
                       #OCastillo 13-07-2022 se incluye busqueda por pasaporte
                       elif  Matricula.objects.filter(Q(inscripcion__persona__cedula=cedula,nivel__cerrado=False)|Q(inscripcion__persona__pasaporte=cedula,nivel__cerrado=False)).exclude(nivel__carrera__nombre='CONGRESO DE PEDAGOGIA').exists():
                       # elif  Persona.objects.filter(cedula=cedula,usuario__groups__id=ALUMNOS_GROUP_ID).exists():
                           persona = Persona.objects.filter(Q(cedula=cedula,usuario__groups__id=ALUMNOS_GROUP_ID,usuario__is_active=True)|Q(pasaporte=cedula,usuario__groups__id=ALUMNOS_GROUP_ID,usuario__is_active=True))[:1].get()
                           if persona.usuario.is_active:
                               if not RetiradoMatricula.objects.filter(inscripcion__persona=persona, activo=False).exists():
                                    tipoatencionbox = TipoAtencionBox.objects.filter(id=1)[:1].get()
                                    if PrecioConsulta.objects.filter(tipovisita=id,tipopersona=2).exists():
                                        precio = PrecioConsulta.objects.filter(tipovisita=id,tipopersona=2)[:1].get()

                       elif Inscripcion.objects.filter(Q(persona__pasaporte=cedula) | Q(persona__cedula=cedula)).exists():
                           persona=Inscripcion.objects.filter(Q(persona__pasaporte=cedula) | Q(persona__cedula=cedula))[:1].get()
                           if persona.persona.usuario.is_active:
                               if not RetiradoMatricula.objects.filter(inscripcion__persona=persona.persona, activo=False).exists():
                                    tipoatencionbox = TipoAtencionBox.objects.filter(id=1)[:1].get()
                                    if PrecioConsulta.objects.filter(tipovisita=id,tipopersona=4).exists():
                                        precio = PrecioConsulta.objects.filter(tipovisita=id,tipopersona=4)[:1].get()

                       elif Persona.objects.filter(cedula=cedula).exclude(usuario__groups__id__in=gruposexcluidos).exists():
                           persona = Persona.objects.filter(cedula=cedula).exclude(usuario__groups__id__in=gruposexcluidos)[:1].get()
                           if PrecioConsulta.objects.filter(tipovisita=id,tipopersona=1).exists():
                                precio = PrecioConsulta.objects.filter(tipovisita=id,tipopersona=1)[:1].get()
                       elif VisitaBox.objects.filter(cedula=cedula).exists():
                           persona = VisitaBox.objects.filter(cedula=cedula)[:1].get()
                           if  PrecioConsulta.objects.filter(tipovisita=id,tipopersona=persona.tipopersona).exists():
                               precio =PrecioConsulta.objects.filter(tipovisita=id,tipopersona=persona.tipopersona)[:1].get()
                       else:
                           cn = psycopg2.connect("host=10.10.9.45 dbname=conduccion user=aok password=R0b3rt0.1tb$") #DATOS DE LA BASE
                           cur = cn.cursor()
                           cur.execute("select distinct auth_group.id as id_grupo "
                                      "from sga_persona,auth_user,auth_user_groups ,auth_group ,sga_matricula,sga_inscripcion,sga_nivel "
                                      "where sga_persona.usuario_id=auth_user.id "
                                      "and auth_user_groups.user_id=auth_user.id "
                                      "and auth_user_groups.group_id=auth_group.id "
                                       "and sga_matricula.inscripcion_id=sga_inscripcion.id "
                                       "and sga_inscripcion.persona_id=sga_persona.id "
                                        "and sga_matricula.nivel_id=sga_nivel.id "
                                        "and sga_nivel.cerrado=False "
                                       "and sga_persona.cedula ='" + cedula +"'")
                           # if cur:
                           dato  = cur.fetchone()
                           cur.close()
                           if dato:
                               con = 0
                               while con <len(dato) :
                                   if dato[con] == 2:
                                       tipopersona = 10
                                       con = len(dato)
                                   elif  dato[con] == 3:
                                       tipopersona = 9
                                       con  = con +1
                                   else:
                                       tipopersona = 8
                                       con = con +1
                               if  PrecioConsulta.objects.filter(tipovisita=id,tipopersona=tipopersona).exists():
                                   precio =PrecioConsulta.objects.filter(tipovisita=id,tipopersona=tipopersona)[:1].get()
                           else:
                               nivelacion = psycopg2.connect("host=10.10.9.45 dbname=sgaonline user=aok password=R0b3rt0.1tb$") #DATOS DE LA BASE
                               curniv = nivelacion.cursor()
                               curniv.execute("select distinct auth_group.id as id_grupo "
                                          "from sga_persona,auth_user,auth_user_groups ,auth_group ,sga_matricula,sga_inscripcion,sga_nivel "
                                          "where sga_persona.usuario_id=auth_user.id "
                                          "and auth_user_groups.user_id=auth_user.id "
                                          "and auth_user_groups.group_id=auth_group.id "
                                           "and sga_matricula.inscripcion_id=sga_inscripcion.id "
                                           "and sga_inscripcion.persona_id=sga_persona.id "
                                            "and sga_matricula.nivel_id=sga_nivel.id "
                                            "and sga_nivel.cerrado=False "
                                           "and sga_persona.cedula ='" + cedula +"'")
                               # if cur:
                               datoniv  = curniv.fetchone()
                               curniv.close()
                               if datoniv:
                                   conniv = 0
                                   while conniv <len(datoniv) :
                                       if datoniv[conniv] == 7:
                                           tipopersona = 12
                                           conniv = len(datoniv)
                                           if  PrecioConsulta.objects.filter(tipovisita=id,tipopersona=tipopersona).exists():
                                                precio =PrecioConsulta.objects.filter(tipovisita=id,tipopersona=tipopersona)[:1].get()

                       if not precio:
                           if PrecioConsulta.objects.filter(tipovisita=id,tipopersona=3).exists():
                               precio = PrecioConsulta.objects.filter(tipovisita=id,tipopersona=3)[:1].get()
                   if  not tipoatencionbox:
                       tipoatencionbox = TipoAtencionBox.objects.filter(id=2)[:1].get()
                   idatencion = tipoatencionbox.id
                   tiket=0
                   sede = None
                   fecha=datetime.now().date()
                   client_address = ip_client_address(request)
                   if Aula.objects.filter(ip=str(client_address),activa=False).exists():
                        sede = Aula.objects.filter(ip=str(client_address),activa=False)[:1].get().sede.id
                   if VisitaTiket.objects.filter(fechatiket=fecha,tipovisitabox=id,tipovisitabox__sede__id=sede).exists():
                      htiket=VisitaTiket.objects.filter(fechatiket=fecha,tipovisitabox=id,tipovisitabox__sede__id=sede)[:1].get()
                      tiket=int(VisitaTiket.objects.filter(fechatiket=fecha,tipovisitabox=id,tipovisitabox__sede__id=sede)[:1].get().totaltiket)+1
                      htiket.totaltiket=tiket
                      htiket.save()
                      if VisTiketDet.objects.filter(visitatiket__id = htiket.id,tipoatencionbox__id=idatencion,visitatiket__tipovisitabox__sede__id=sede).exists():
                          tiket = int(VisTiketDet.objects.filter(visitatiket__id = htiket.id,tipoatencionbox__id=idatencion,visitatiket__tipovisitabox__sede__id=sede).order_by('-id')[:1].get().tiket)+1
                          dtiket = VisTiketDet(visitatiket_id = htiket.id,tiket=tiket,horatiket=datetime.now(),atendido=False,tipoatencionbox_id=idatencion)
                          dtiket.save()
                      else:
                          tiket=1
                          dtiket = VisTiketDet(visitatiket_id = htiket.id,tiket=1,horatiket=datetime.now(),atendido=False,tipoatencionbox_id=idatencion)
                          dtiket.save()
                   else:
                      tiket=1
                      htiket = VisitaTiket(tipovisitabox_id=id,fechatiket=datetime.now().date(),totaltiket=tiket)
                      htiket.save()
                      dtiket = VisTiketDet(visitatiket_id = htiket.id,tiket=tiket,horatiket=datetime.now(),atendido=False,tipoatencionbox_id=idatencion)
                      dtiket.save()

                   if precio:

                       if precio.precio > 0:
                          tipootro = TipoOtroRubro.objects.get(pk=14)
                          inscripcion = Inscripcion.objects.get(pk=CONSUMIDOR_FINAL)
                          rubro = Rubro(fecha=datetime.now().date(), valor=float( precio.precio),
                                  inscripcion=inscripcion, cancelado=False, fechavence=datetime.now().date())
                          rubro.save()
                          rubrootro = RubroOtro(rubro=rubro, tipo=tipootro, descripcion='CONSULTA ' + str(precio.tipovisita.descripcion) + " - " + cedula )
                          rubrootro.save()
                          #OCastillo 15-06-2022 nueva tabla para ver citas pagadas
                          citascanceladas=CitasCancelasBox(cedula=cedula,tipovisita_id=id,rubro=rubro)
                          citascanceladas.save()
                          return HttpResponse(json.dumps({"result":"ok","horacita":horacita,"tiket":tiket,"ABR":TipoVisitasBox.objects.filter(id=id)[:1].get().visor+tipoatencionbox.descripcion[0],"pre": "</br> $" + str(precio.precio)}),content_type="application/json")
                       else:
                           return HttpResponse(json.dumps({"result":"ok","horacita":horacita,"tiket":tiket,"ABR":TipoVisitasBox.objects.filter(id=id)[:1].get().visor+tipoatencionbox.descripcion[0],"pre":""}),content_type="application/json")
                   return HttpResponse(json.dumps({"result":"ok","horacita":horacita,"tiket":tiket,"ABR":TipoVisitasBox.objects.filter(id=id)[:1].get().visor+tipoatencionbox.descripcion[0],"pre":""}),content_type="application/json")
           except Exception as e:
               return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

        if action=='print2':
           id=request.POST['idvisita']
           idatencion=request.POST['idatencion']
           tipoatencionbox = TipoAtencionBox.objects.filter(id=idatencion)[:1].get()
           tiket=0
           fecha=datetime.now().date()
           if VisitaTiket.objects.filter(fechatiket=fecha,tipovisitabox=id).exists():
              htiket=VisitaTiket.objects.filter(fechatiket=fecha,tipovisitabox=id)[:1].get()
              tiket=int(VisitaTiket.objects.filter(fechatiket=fecha,tipovisitabox=id)[:1].get().totaltiket)+1
              htiket.totaltiket=tiket
              htiket.save()
              if VisTiketDet.objects.filter(visitatiket__id = htiket.id,tipoatencionbox__id=idatencion).exists():
                  tiket = int(VisTiketDet.objects.filter(visitatiket__id = htiket.id,tipoatencionbox__id=idatencion).order_by('-id')[:1].get().tiket)+1
                  dtiket = VisTiketDet(visitatiket_id = htiket.id,tiket=tiket,horatiket=datetime.now(),atendido=False,tipoatencionbox_id=idatencion)
                  dtiket.save()
              else:
                  tiket=1
                  dtiket = VisTiketDet(visitatiket_id = htiket.id,tiket=1,horatiket=datetime.now(),atendido=False,tipoatencionbox_id=idatencion)
                  dtiket.save()
           else:
              tiket=1
              htiket = VisitaTiket(tipovisitabox_id=id,fechatiket=datetime.now().date(),totaltiket=tiket)
              htiket.save()
              dtiket = VisTiketDet(visitatiket_id = htiket.id,tiket=tiket,horatiket=datetime.now(),atendido=False,tipoatencionbox_id=idatencion)
              dtiket.save()


           return HttpResponse(json.dumps({"result":"ok","tiket":tiket,"ABR":TipoVisitasBox.objects.filter(id=id)[:1].get().visor+tipoatencionbox.descripcion[0]}),content_type="application/json")
    else:
        data = {'title': 'Impresion de Tikets'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='print': #********   Genera el nuevo Tiket    ***************
                a=''
        else:
            data['newstiket'] = NewsTiket.objects.filter().exclude(estadonoticia=False)
            sede = 0
            client_address = ip_client_address(request)
            if Aula.objects.filter(ip=str(client_address),activa=False).exists():
                sede = Aula.objects.filter(ip=str(client_address),activa=False)[:1].get().sede.id
            data['tipovisitabox'] = TipoVisitasBox.objects.filter(sede__id=sede).exclude(alias=None).exclude(alias='').exclude(estado=False)
            data['tipoatencionbox'] = TipoAtencionBox.objects.all()
            return render(request ,"visitabtiket/visitabtiket.html" ,  data)