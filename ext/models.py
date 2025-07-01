from django.db import models
from sga.models import *
import requests
from settings import RUBRO_TIPO_OTRO_INSCRIPCION, RUBRO_TIPO_OTRO_MODULO_EXTERNO, RUBRO_TIPO_OTRO_MODULO_INTERNO, RUBRO_TIPO_OTRO_LIBRO, RUBRO_TIPO_OTRO_CD, RUBRO_TIPO_OTRO_LIBRO2

def convertir_fecha(s):
    try:
        return datetime(int(s[-4:]), int(s[3:5]), int(s[:2]))
    except:
        return datetime.now()

# Create your models here.
class EntidadImportacion(models.Model):
    nombre = models.CharField(max_length=300)
    url = models.CharField(max_length=300)
    codigo = models.CharField(max_length=3)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return str(self.nombre)

    def importar_datos(self):
        asignaturas = self.asignaturaexterna_set.all()
        valores = ','.join([str(x.asignaturaext) for x in asignaturas])
        data = {'asig': valores}
        materiacreada = 0
        inscripcionescreadas = 0
        materiasasigandascreadas = 0
        error = 0
        try:
            r = requests.get(self.url+'/api?a=impmaterias', params=data)
            j = r.json()
            mate = j.keys()
            rubromodulo = TipoOtroRubro.objects.filter(id=RUBRO_TIPO_OTRO_MODULO_EXTERNO)[:1].get()

            for i in mate:
                gr = j[i]
                materiainfo = gr[0]
                if materiainfo['id']:
                    inicio = materiainfo['inicio']
                    fin = materiainfo['fin']
                    asignaturaexterna = materiainfo['asignatura']
                    materiaidexterna = materiainfo['id']
                    paralelo = materiainfo['paralelo']
                    if self.codigo == 'ITB':
                        if paralelo[0]=='E' or paralelo[0]=='P'  or paralelo[0]=='G' :
                            rubrolibros = TipoOtroRubro.objects.filter(id=RUBRO_TIPO_OTRO_LIBRO)[:1].get()
                        else:
                            rubrolibros = TipoOtroRubro.objects.filter(id=RUBRO_TIPO_OTRO_LIBRO2)[:1].get()
                    else:
                        rubrolibros = TipoOtroRubro.objects.filter(id=RUBRO_TIPO_OTRO_LIBRO2)[:1].get()
                    if AsignaturaExterna.objects.filter(entidad=self, asignaturaext=asignaturaexterna).exists():
                        asig=AsignaturaExterna.objects.filter(entidad=self, asignaturaext=asignaturaexterna)[:1].get().asignatura
                        if not MateriaExterna.objects.filter(entidad=self, materia__asignatura=asig,codigo=paralelo ).exists():
                            asignaturalocal = AsignaturaExterna.objects.filter(entidad=self, asignaturaext=asignaturaexterna)[:1].get().asignatura
                            nivel = Nivel.objects.filter()[:1].get()
                            try:
                                materianueva = Materia( asignatura = asignaturalocal,
                                                        nivel = nivel,
                                                        horas = 0,
                                                        creditos = 0,
                                                        inicio = convertir_fecha(inicio),
                                                        fin = convertir_fecha(fin))
                                materianueva.save()

                                materiaexterna = MateriaExterna(entidad=self,
                                                                materia=materianueva,
                                                                materiaexterna=materiaidexterna,
                                                                codigo=paralelo,
                                                                cantexport= 0)
                                materiaexterna.save()
                                materiacreada += 1
                            except Exception as ex:
                                error = str(ex)
                                pass
                        else:
                            materianueva = MateriaExterna.objects.filter(entidad=self, materia__asignatura=asig,codigo=paralelo)[:1].get().materia

                            # inscripciones
                        alum = gr[1]
                        gpe = alum.keys()
                        for gp in gpe:
                            pe = alum[gp]
                            for inscrip in pe:
                                datoskeys = inscrip.keys()
                                for datoskey in datoskeys:
                                    i =  inscrip[datoskey]
                                    extranjero=False
                                    # print(str(i))
                                    b=0
                                    try:
                                        if i[0]['cedula'] or i[0]['extranjero']:
                                            # persona
                                            cedula = i[0]['cedula']
                                            if i[0]['pasaporte']:
                                                pasaporte = i[0]['pasaporte']
                                                extranjero =i[0]['extranjero']
                                            # OC 06/05/2014 para validar estudiantes extranjeros
                                            if cedula.lstrip().__len__() > 0 or extranjero :
                                                if extranjero:
                                                    if not Persona.objects.filter(pasaporte=pasaporte).exists():
                                                        alu_persona = Persona(  nombres = i[0]['nombres'],
                                                                                apellido1 = i[0]['apellido1'],
                                                                                apellido2 = i[0]['apellido2'],
                                                                                cedula = i[0]['cedula'],
                                                                                pasaporte = i[0]['pasaporte'],
                                                                                extranjero=i[0]['extranjero'],
                                                                                direccion = i[0]['direccion'],
                                                                                direccion2 = i[0]['direccion2'],
                                                                                telefono = i[0]['telefono'],
                                                                                telefono_conv = i[0]['telefono_conv'],
                                                                                email = i[0]['email'])
                                                    else:
                                                        alu_persona = Persona.objects.filter(pasaporte=i[0]['pasaporte'])[:1].get()
                                                        alu_persona.apellido1 = i[0]['apellido1']
                                                        alu_persona.apellido2 = i[0]['apellido2']
                                                        alu_persona.nombres = i[0]['nombres']
                                                        alu_persona.cedula = i[0]['cedula']
                                                        alu_persona.pasaporte = i[0]['pasaporte']
                                                        alu_persona.extranjero = i[0]['extranjero']
                                                        alu_persona.direccion = i[0]['direccion']
                                                        alu_persona.direccion2 = i[0]['direccion2']
                                                        alu_persona.telefono = i[0]['telefono']
                                                        alu_persona.telefono_conv = i[0]['telefono_conv']
                                                        alu_persona.email = i[0]['email']

                                                    alu_persona.save()

                                                if not Persona.objects.filter(cedula=cedula ).exists():
                                                    alu_persona = Persona(  nombres = i[0]['nombres'],
                                                                            apellido1 = i[0]['apellido1'],
                                                                            apellido2 = i[0]['apellido2'],
                                                                            cedula = i[0]['cedula'],
                                                                            pasaporte = i[0]['pasaporte'],
                                                                            extranjero = i[0]['extranjero'],
                                                                            direccion = i[0]['direccion'],
                                                                            direccion2 = i[0]['direccion2'],
                                                                            telefono = i[0]['telefono'],
                                                                            telefono_conv = i[0]['telefono_conv'],
                                                                            email = i[0]['email'])
                                                else:
                                                    if not extranjero:
                                                        alu_persona = Persona.objects.filter(cedula=i[0]['cedula'])[:1].get()
                                                        alu_persona.apellido1 = i[0]['apellido1']
                                                        alu_persona.apellido2 = i[0]['apellido2']
                                                        alu_persona.nombres = i[0]['nombres']
                                                        alu_persona.cedula = i[0]['cedula']
                                                        alu_persona.direccion = i[0]['direccion']
                                                        alu_persona.direccion2 = i[0]['direccion2']
                                                        alu_persona.telefono = i[0]['telefono']
                                                        alu_persona.telefono_conv = i[0]['telefono_conv']
                                                        alu_persona.email = i[0]['email']

                                                alu_persona.save()

                                                #inscripcion
                                                session = Sesion.objects.filter()[:1].get()
                                                modalidad = Modalidad.objects.filter()[:1].get()
                                                carrera = Carrera.objects.filter()[:1].get()
                                                especialidad = Especialidad.objects.filter()[:1].get()
                                                if not Inscripcion.objects.filter(persona=alu_persona).exists():
                                                    alu_inscrip = Inscripcion(  persona = alu_persona,
                                                                                fecha = datetime.now(),
                                                                                carrera = carrera,
                                                                                modalidad = modalidad,
                                                                                sesion = session,
                                                                                especialidad = especialidad)
                                                    alu_inscrip.save()
                                                    inscripcionescreadas += 1
                                                    #rubros libro
                                                    r2 = Rubro( fecha = materianueva.inicio,
                                                                valor = rubrolibros.precio_sugerido(),
                                                                inscripcion = alu_inscrip,
                                                                cancelado = False,
                                                                fechavence = materianueva.fin)
                                                    r2.save()

                                                    r2otro = RubroOtro(rubro=r2,
                                                                       # tipo=TipoOtroRubro.objects.get(pk=RUBRO_TIPO_OTRO_LIBRO)
                                                                       # OCU 22-08-2018 para que tome el id que indica el costo segun la carrera
                                                                       tipo=TipoOtroRubro.objects.get(pk=rubrolibros.id),
                                                                       descripcion=materianueva.nombre_completo()+" - "+materianueva.materia_externa().codigo)
                                                    r2otro.save()

                                                    r1 = Rubro( fecha = materianueva.inicio,
                                                                valor = rubromodulo.precio_sugerido(),
                                                                inscripcion = alu_inscrip,
                                                                cancelado = False,
                                                                fechavence = materianueva.fin)
                                                    r1.save()
                                                    r1otro = RubroOtro(rubro=r1,
                                                                       tipo=TipoOtroRubro.objects.get(pk=RUBRO_TIPO_OTRO_MODULO_EXTERNO),
                                                                       descripcion=materianueva.nombre_completo()+" - "+materianueva.materia_externa().codigo,
                                                                       extra=str(asignaturalocal.id))
                                                    r1otro.save()
                                                else:
                                                    alu_inscrip = Inscripcion.objects.filter(persona=alu_persona)[:1].get()
                                                    alu_inscrip.fecha = datetime.now()
                                                    alu_inscrip.carrera = carrera
                                                    alu_inscrip.modalidad = modalidad
                                                    alu_inscrip.sesion = session
                                                    alu_inscrip.especialidad = especialidad

                                                    #   aqui para que se actualicen los rubros con el nuevo valor del libro OCU 22-08-2018
                                                    # if RubroOtro.objects.filter(rubro__inscripcion=alu_inscrip,tipo=RUBRO_TIPO_OTRO_LIBRO).exists():
                                                    #     rubroest=RubroOtro.objects.filter(rubro__inscripcion=alu_inscrip,tipo=RUBRO_TIPO_OTRO_LIBRO)
                                                    #     for rbest in rubroest:
                                                    #         if Rubro.objects.filter(pk=rbest.rubro.id,cancelado=False,fecha__gte='2018-08-20').exists():
                                                    #             rubroact=Rubro.objects.filter(pk=rbest.rubro.id,cancelado=False,fecha__gte='2018-08-20')[:1].get()
                                                    #             if rubroact.valor==25:
                                                    #                 rubroact.valor=rubromodulo.precio_sugerido()
                                                    #                 rubroact.save()
                                                    # else:
                                                    #     if RubroOtro.objects.filter(rubro__inscripcion=alu_inscrip,tipo=rubrolibros.id).exists():
                                                    #         rubroest=RubroOtro.objects.filter(rubro__inscripcion=alu_inscrip,tipo=rubrolibros.id)
                                                    #         for rbest in rubroest:
                                                    #             if Rubro.objects.filter(pk=rbest.rubro.id,cancelado=False,fecha__gte='2018-08-20').exists():
                                                    #                 rubroact=Rubro.objects.filter(pk=rbest.rubro.id,cancelado=False,fecha__gte='2018-08-20')[:1].get()
                                                    #                 if rubroact.valor==25:
                                                    #                     rubroact.valor=rubromodulo.precio_sugerido()
                                                    #                     rubroact.save()

                                                    # hasta aqui OCU 22-08-2018 ojojojo

                                                #matricula
                                                nivel = Nivel.objects.filter()[:1].get()
                                                if not Matricula.objects.filter(inscripcion=alu_inscrip, nivel=nivel).exists():

                                                    alu_matricul = Matricula(   inscripcion = alu_inscrip,
                                                                                nivel = nivel)
                                                    alu_matricul.save()
                                                else:
                                                    alu_matricul = Matricula.objects.filter(inscripcion=alu_inscrip, nivel=nivel)[:1].get()
                                                    # Actualizacion de Grupo
                                                    if AsignaturaExterna.objects.filter(entidad=self, asignaturaext=asignaturaexterna).exists():
                                                        asignaturalocal = AsignaturaExterna.objects.filter(entidad=self, asignaturaext=asignaturaexterna)[:1].get().asignatura
                                                        if MateriaAsignada.objects.filter(matricula=alu_matricul,materia__asignatura=asignaturalocal).exists():
                                                            materiaasig = MateriaAsignada.objects.filter(matricula=alu_matricul,materia__asignatura=asignaturalocal)[:1].get()
                                                            if MateriaExterna.objects.filter(materia=materiaasig.materia).exists():
                                                                paraleloact=MateriaExterna.objects.filter(materia=materiaasig.materia)[:1].get().codigo
                                                                if not paraleloact == paralelo:
                                                                    if MateriaExterna.objects.filter(codigo=paralelo).exists():
                                                                        materiaact = MateriaExterna.objects.filter(codigo=paralelo)[:1].get()
                                                                        materiaasig.materia = materiaact.materia
                                                                        materiaasig.save()
                                                                        b=1
                                                        else:
                                                            if not MateriaAsignada.objects.filter(matricula=alu_matricul,materia__asignatura=asignaturalocal).exists():
                                                                alu_materia = MateriaAsignada(  matricula = alu_matricul,
                                                                                            materia = materianueva,
                                                                                            notafinal = 0,
                                                                                            asistenciafinal = 0,
                                                                                            supletorio = 0,
                                                                                            cerrado = False)
                                                                alu_materia.save()
                                                            # rubro modulo
                                                            ban=0
                                                            rubroa = RubroOtro.objects.filter(rubro__inscripcion=alu_inscrip)
                                                            for r in rubroa:
                                                                if r.extra == str(asignaturalocal.id):
                                                                    ban=1
                                                            if ban==0:
                                                                r1 = Rubro( fecha = materianueva.inicio,
                                                                            valor = rubromodulo.precio_sugerido(),
                                                                            inscripcion = alu_inscrip,
                                                                            cancelado = False,
                                                                            fechavence = materianueva.fin)
                                                                r1.save()
                                                                r1otro = RubroOtro(rubro=r1,
                                                                                   tipo=TipoOtroRubro.objects.get(pk=RUBRO_TIPO_OTRO_MODULO_EXTERNO),
                                                                                   descripcion=materianueva.nombre_completo()+" - "+materianueva.materia_externa().codigo,
                                                                                   extra=str(asignaturalocal.id))
                                                                r1otro.save()

                                                #materia asignada
                                                if not MateriaAsignadaExterna.objects.filter(entidad=self, materiaasignadaexterna=i[0]['materiaasignada']).exists():
                                                    if b==0:
                                                        if not MateriaAsignada.objects.filter(materia=materianueva,matricula = alu_matricul).exists():
                                                            alu_materia = MateriaAsignada(  matricula = alu_matricul,
                                                                                            materia = materianueva,
                                                                                            notafinal = 0,
                                                                                            asistenciafinal = 0,
                                                                                            supletorio = 0,
                                                                                            cerrado = False)
                                                            alu_materia.save()
                                                        else:
                                                            alu_materia = MateriaAsignada.objects.filter(materia=materianueva,matricula = alu_matricul)[:1].get()
                                                        if not MateriaAsignadaExterna.objects.filter(entidad=self, materiaasignadaexterna=i[0]['materiaasignada']).exists():
                                                            alu_materiaexterna = MateriaAsignadaExterna(entidad = self,
                                                                                                        materiaasignada = alu_materia,
                                                                                                        materiaasignadaexterna = i[0]['materiaasignada'])
                                                            alu_materiaexterna.save()

                                                            materiasasigandascreadas += 1
                                                else:
                                                        MateriaAsignadaExterna.objects.filter(entidad=self, materiaasignadaexterna=i[0]['materiaasignada'])[:1].get()

                                    except Exception as ex:
                                        pass
                                        error = str(ex)
        except Exception as ex:
            pass
            error = str(ex)
        return {"ma":materiacreada,"ins":inscripcionescreadas,"maa":materiasasigandascreadas,"err":error}

class AsignaturaExterna(models.Model):
    entidad = models.ForeignKey(EntidadImportacion, on_delete=models.CASCADE)
    asignatura =  models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    asignaturaext = models.IntegerField()

class MateriaExterna(models.Model):
    entidad = models.ForeignKey(EntidadImportacion, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    materiaexterna = models.IntegerField()
    codigo = models.CharField(max_length=30, blank=True, null=True)
    exportada = models.BooleanField()
    cantexport = models.IntegerField()

    def materia_entidad(self):
        return MateriaExterna.objects.filter(materia=self.materia)[:1].get().entidad.nombre

    def correo_noexporta(self,cant,datos):
        if self.entidad.codigo == 'ITF':
            tipo = TipoIncidencia.objects.get(pk=2)
        else:
            tipo = TipoIncidencia.objects.get(pk=1)
        hoy = datetime.now().today()
        contenido = "NOTIFICACION INGLES"
        send_html_mail("OCURRIERON ERRORES EN LA EXPORTACION",
            "emails/noexportada.html", {'d': self, 'fecha': hoy,'datos':datos.split(",")[:cant]},tipo.correo.split(","))


    def enviar_correo(self):
        try:
            r = requests.post(self.entidad.url+'/api?a=enviacorreo&maa='+str(self.materiaexterna)+'&cant_export='+str(self.cantexport),verify=False)
        except Exception as ex:
            mensaje=str(ex)
            error=str(ex)

    def exportar_datos(self):
        error = 0
        mensaje = ""
        datos = ""
        matasii = 0
        try:
            if self.materia.cerrado:
                data = {}
                ma = self.materia.materiaasignada_set.all()
                total_warnig = 0
                total_error = 0
                if MODELO_EVALUACION == EVALUACION_ITB:
                    #materia externa
                    for mai in ma:
                        if mai.materiaasignadaexterna_set.exists():
                            # materia asignada externa
                            maie = mai.materiaasignadaexterna_set.all()[:1].get()
                            evaluacion  = EvaluacionITB.objects.filter(materiaasignada=mai)[:1].get()
                            try:

                                r = requests.post(self.entidad.url+'/api?a=actualizamateriaasignada&maa='+str(maie.materiaasignadaexterna)+'&cod1='+str(evaluacion.cod1_id)+'&cod2='+str(evaluacion.cod2_id)+'&cod3='+str(evaluacion.cod3_id)+'&cod4='+str(evaluacion.cod4_id)+'&n1='+str(evaluacion.n1)+'&n2='+str(evaluacion.n2)+'&n3='+str(evaluacion.n3)+'&n4='+str(evaluacion.n4)+'&examen='+str(evaluacion.examen)+'&recuperacion='+str(evaluacion.recuperacion))
                            except Exception as ex:
                                mensaje=str(ex)
                                error=str(ex)

                            j = r.json()
                            matasii = maie.materiaasignadaexterna
                            if j.has_key('error'):
                                tipo_error = j['error']
                                if tipo_error==1:
                                    mensaje += ", Err:"+mai.matricula.inscripcion.persona.nombre_completo()
                                    total_error += 1
                            if j.has_key('warning'):
                                tipo_error = j['warning']
                                if tipo_error==1:

                                    mensaje += ", Wrn:"+mai.matricula.inscripcion.persona.nombre_completo()
                                    total_warnig += 1
                                    datos += mai.matricula.inscripcion.persona.nombre_completo() + " N1:" + str(evaluacion.n1) + " - N2:" + str(evaluacion.n2)  + " - N3:" + str(evaluacion.n3) + " - N4:" + str(evaluacion.n4) + " - Examen:" + str(evaluacion.examen) + " - Recup:" + str(evaluacion.recuperacion) +  ","
                    # cierra la materia
                    if total_error==0:
                        data['ma'] = self.materiaexterna
                        r = requests.post(self.entidad.url+'/api?a=cerrarmateria&ma='+str(self.materiaexterna)+'&matasii='+str(matasii),verify=False)
                        j = r.json()
                        if j.has_key('error'):
                            tipo_error = j['error']
                            if tipo_error==1:
                                error = 4
                                mensaje += ", (NO SE PUDO CERRAR LA MATERIA)"
                                self.exportada = False
                            if tipo_error==0:
                                error = 0
                                mensaje += " EXPORTACION OK. MATERIA CERRADA CORRECTAMENTE."
                                self.exportada = True
                            self.save()
                        else:
                            # no retorno el valor de confirmacion
                            error = 3
                    else:
                        # existen errores en la actualizacion de materiasasignadas
                        error = 3
            else:
                #materia no cerrada todavia
                error = 2
        except Exception as ex:
            #algun otro error en la exportacion
            error = str(ex)

        return {"err":error,"mensaje":mensaje,"ma":self.materia.id,'tot_wrn':total_warnig,'datos':datos}

class MateriaAsignadaExterna(models.Model):
    entidad = models.ForeignKey(EntidadImportacion, on_delete=models.CASCADE)
    materiaasignada = models.ForeignKey(MateriaAsignada, on_delete=models.CASCADE)
    materiaasignadaexterna = models.IntegerField()



