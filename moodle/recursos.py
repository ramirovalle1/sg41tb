import sys
import time
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db import connections, transaction, connection
from moodle.config import MY_PRIFIX_MOODLE
from sga.models import (Materia, Persona, DiapositivaSilaboSemanal, CompendioSilaboSemanal,
                        VideoMagistralSilaboSemanal, GuiaEstudianteSilaboSemanal, TestSilaboSemanal,
                        ForoSilaboSemanal, TareaSilaboSemanal)
from moodle.core import ElementosMoodle, CategoriasMoodle
from moodle.functions import get_user_detail_by_username, crear_usuario, crear_actualizar_categoria_notas_curso
from settings import DEBUG
from sga.funciones import null_to_numeric


class GestionMoodle:

    def __init__(self, eMateria:Materia, ePersona:Persona):
        self.eMateria = eMateria
        self.ePersona = ePersona
        self.eNivel = self.eMateria.nivel
        self.eConfig = self.eNivel.eva

        if not self.eConfig:
            raise ValueError("No existe configuración EVA para el nivel")
        if not self.eConfig.has_web_service_data():
            raise ValueError(
                "No existe configuración EVA para migrar datos: Complete datos de URL, Prefijo, Token, Roles, Categoría"
            )

        self.prefix = self.eConfig.prefix_db or MY_PRIFIX_MOODLE
        self.connection_eva = self.eConfig.type_connection

        if self.connection_eva == self.eConfig.TypesConnections.NINGUNA:
            raise ValueError("No se encuentra configurada la conexión a EVA")

        self.id_moodle_course = eMateria.id_moodle_course

        if not self.id_moodle_course:
            raise ValueError("No se encuentra creado el curso en EVA")

        self.cursor = connections[self.connection_eva].cursor()
        # Obtén el nombre del motor de la base de datos para la conexión predeterminada
        self.db_vendor = connections[self.connection_eva].vendor
        username = self.ePersona.usuario.username
        user_id = get_user_detail_by_username(username, self.cursor, 'id', self.prefix)
        if user_id is None:
            isSuccess, message, user_id = crear_usuario(self.cursor, self.ePersona, self.prefix)
            if not isSuccess:
                raise ValueError(message)
        if not user_id:
            raise ValueError("Usuario no encontrado en EVA")
        self.id_moodle_user = user_id

    def actualizar_html(self):
        eMateria = self.eMateria
        eMateria.actualizar_moodle_html=True
        eMateria.save()

    def migrar_presentacion(self, eDiapositivaSilaboSemanal:DiapositivaSilaboSemanal):
        self.actualizar_html()
        with transaction.atomic(using=self.connection_eva):
            try:
                section = self._get_section(CategoriasMoodle.PRESENTACIONES)
                intro = eDiapositivaSilaboSemanal.descripcion.replace("'", "")
                if eDiapositivaSilaboSemanal.tipomaterial == 1:
                    url = f'https://sga.itb.edu.ec{eDiapositivaSilaboSemanal.archivodiapositiva.url}'
                else:
                    url = eDiapositivaSilaboSemanal.url
                fecha = int(time.mktime(datetime.now().timetuple()))
                nombre_diplay = "S%s-%s" % (eDiapositivaSilaboSemanal.silabosemanal.numsemana, eDiapositivaSilaboSemanal.nombre.replace("'", '')[:252])
                if eDiapositivaSilaboSemanal.id_recurso_moodle <= 0:
                    instance_id = self._insert_url(section, intro, url, fecha, nombre_diplay)
                    eDiapositivaSilaboSemanal.id_recurso_moodle = instance_id
                    eDiapositivaSilaboSemanal.estado_id = 4
                    eDiapositivaSilaboSemanal.migrado = True
                    eDiapositivaSilaboSemanal.save()
                else:
                    instance_id = eDiapositivaSilaboSemanal.id_recurso_moodle
                    self._update_url(instance_id, nombre_diplay, intro, url, fecha)
                    eDiapositivaSilaboSemanal.id_recurso_moodle = instance_id
                    eDiapositivaSilaboSemanal.estado_id = 4
                    eDiapositivaSilaboSemanal.migrado = True
                    eDiapositivaSilaboSemanal.save()

                return True, "Recurso migrado a Moodle"
            except Exception as ex:
                transaction.set_rollback(True, using=self.connection_eva)
                return False, f"{str(ex)} - {sys.exc_info()[-1].tb_lineno}"
            finally:
                self.cursor.close()

    def migrar_compendio(self, eCompendioSilaboSemanal:CompendioSilaboSemanal):
        self.actualizar_html()
        with transaction.atomic(using=self.connection_eva):
            try:
                section = self._get_section(CategoriasMoodle.COMPENDIOS)
                intro = eCompendioSilaboSemanal.descripcion.replace("'", "")
                url = f'https://sga.itb.edu.ec{eCompendioSilaboSemanal.archivocompendio.url}'
                fecha = int(time.mktime(datetime.now().timetuple()))
                nombre_diplay = "S%s-%s-Compendio" % (eCompendioSilaboSemanal.silabosemanal.numsemana, eCompendioSilaboSemanal.nombre.replace("'", '')[:252])
                if eCompendioSilaboSemanal.id_recurso_moodle <= 0:
                    instance_id = self._insert_url(section, intro, url, fecha, nombre_diplay)
                    eCompendioSilaboSemanal.id_recurso_moodle = instance_id
                    eCompendioSilaboSemanal.estado_id = 4
                    eCompendioSilaboSemanal.migrado = True
                    eCompendioSilaboSemanal.save()
                else:
                    instance_id = eCompendioSilaboSemanal.id_recurso_moodle
                    self._update_url(instance_id, nombre_diplay, intro, url, fecha)
                    eCompendioSilaboSemanal.id_recurso_moodle = instance_id
                    eCompendioSilaboSemanal.estado_id = 4
                    eCompendioSilaboSemanal.migrado = True
                    eCompendioSilaboSemanal.save()

                return True, "Recurso migrado a Moodle"
            except Exception as ex:
                transaction.set_rollback(True, using=self.connection_eva)
                return False, f"{str(ex)} - {sys.exc_info()[-1].tb_lineno}"
            finally:
                self.cursor.close()

    def migrar_video_magistral(self, eVideoMagistralSilaboSemanal:VideoMagistralSilaboSemanal):
        self.actualizar_html()
        with transaction.atomic(using=self.connection_eva):
            try:
                section = self._get_section(CategoriasMoodle.VIDEOS_MAGISTRALES)
                intro = eVideoMagistralSilaboSemanal.descripcion.replace("'", "")
                if eVideoMagistralSilaboSemanal.tipomaterial == 1:
                    url = f'https://sga.itb.edu.ec{eVideoMagistralSilaboSemanal.archivovideo.url}'
                else:
                    url = eVideoMagistralSilaboSemanal.url
                fecha = int(time.mktime(datetime.now().timetuple()))
                nombre_diplay = "S%s-%s" % (eVideoMagistralSilaboSemanal.silabosemanal.numsemana, eVideoMagistralSilaboSemanal.nombre.replace("'", '')[:252])
                if eVideoMagistralSilaboSemanal.id_recurso_moodle <= 0:
                    instance_id = self._insert_url(section, intro, url, fecha, nombre_diplay)
                    eVideoMagistralSilaboSemanal.id_recurso_moodle = instance_id
                    eVideoMagistralSilaboSemanal.estado_id = 4
                    eVideoMagistralSilaboSemanal.migrado = True
                    eVideoMagistralSilaboSemanal.save()
                else:
                    instance_id = eVideoMagistralSilaboSemanal.id_recurso_moodle
                    self._update_url(instance_id, nombre_diplay, intro, url, fecha)
                    eVideoMagistralSilaboSemanal.id_recurso_moodle = instance_id
                    eVideoMagistralSilaboSemanal.estado_id = 4
                    eVideoMagistralSilaboSemanal.migrado = True
                    eVideoMagistralSilaboSemanal.save()

                return True, "Recurso migrado a Moodle"
            except Exception as ex:
                transaction.set_rollback(True, using=self.connection_eva)
                return False, f"{str(ex)} - {sys.exc_info()[-1].tb_lineno}"
            finally:
                self.cursor.close()

    def migrar_guia_estudiante(self, eGuiaEstudianteSilaboSemanal:GuiaEstudianteSilaboSemanal):
        self.actualizar_html()
        with transaction.atomic(using=self.connection_eva):
            try:
                section = self._get_section(CategoriasMoodle.GUIAS_DEL_ESTUDIANTE)
                intro = eGuiaEstudianteSilaboSemanal.objetivo.replace("'", "")
                url = f'https://sga.itb.edu.ec{eGuiaEstudianteSilaboSemanal.archivoguiaestudiante.url}'

                fecha = int(time.mktime(datetime.now().timetuple()))
                nombre_diplay = "S%s-%s-Guía Estudiante" % (eGuiaEstudianteSilaboSemanal.silabosemanal.numsemana, eGuiaEstudianteSilaboSemanal.nombre.replace("'", '')[:252])
                if eGuiaEstudianteSilaboSemanal.id_recurso_moodle <= 0:
                    instance_id = self._insert_url(section, intro, url, fecha, nombre_diplay)
                    eGuiaEstudianteSilaboSemanal.id_recurso_moodle = instance_id
                    eGuiaEstudianteSilaboSemanal.estado_id = 4
                    eGuiaEstudianteSilaboSemanal.migrado = True
                    eGuiaEstudianteSilaboSemanal.save()
                else:
                    instance_id = eGuiaEstudianteSilaboSemanal.id_recurso_moodle
                    self._update_url(instance_id, nombre_diplay, intro, url, fecha)
                    eGuiaEstudianteSilaboSemanal.id_recurso_moodle = instance_id
                    eGuiaEstudianteSilaboSemanal.estado_id = 4
                    eGuiaEstudianteSilaboSemanal.migrado = True
                    eGuiaEstudianteSilaboSemanal.save()

                return True, "Recurso migrado a Moodle"
            except Exception as ex:
                transaction.set_rollback(True, using=self.connection_eva)
                return False, f"{str(ex)} - {sys.exc_info()[-1].tb_lineno}"
            finally:
                self.cursor.close()

    def migrar_test(self, eTestSilaboSemanal:TestSilaboSemanal):
        self.actualizar_html()
        with transaction.atomic(using=self.connection_eva):
            try:
                section = self._get_section(CategoriasMoodle.ACTIVIDAD_CONTACTO_DOCENTE)

                # Calcular tiempos
                horadesde = eTestSilaboSemanal.desde.hour if eTestSilaboSemanal.desde else 0
                minutodesde = eTestSilaboSemanal.desde.minute if eTestSilaboSemanal.desde else 0
                horahasta = eTestSilaboSemanal.hasta.hour if eTestSilaboSemanal.hasta else 23
                minutohasta = eTestSilaboSemanal.hasta.minute if eTestSilaboSemanal.hasta else 59

                fecha = int(time.mktime(datetime.now().timetuple()))
                fechadesde = datetime(
                    eTestSilaboSemanal.desde.year,
                    eTestSilaboSemanal.desde.month,
                    eTestSilaboSemanal.desde.day,
                    horadesde, minutodesde
                )
                fechahasta = datetime(
                    eTestSilaboSemanal.hasta.year,
                    eTestSilaboSemanal.hasta.month,
                    eTestSilaboSemanal.hasta.day,
                    horahasta, minutohasta
                )
                fechadesde = int(time.mktime(fechadesde.timetuple()))
                fechahasta = int(time.mktime(fechahasta.timetuple()))

                limitetiempo = eTestSilaboSemanal.tiempoduracion * 60

                # Preparar datos para la inserción
                intro = u"<p>%s <br> %s</p>" % (eTestSilaboSemanal.instruccion, eTestSilaboSemanal.recomendacion)
                intro = intro.replace("'", "''")
                nota_maxima = eTestSilaboSemanal.detallemodelo.nota_maxima if eTestSilaboSemanal.calificar else 0
                navegacion = 'free' if eTestSilaboSemanal.navegacion == 1 else 'sequential'
                nombre = eTestSilaboSemanal.nombre
                vecesintento = eTestSilaboSemanal.vecesintento
                calificar = eTestSilaboSemanal.calificar
                detallemodelo_nombre = eTestSilaboSemanal.detallemodelo.nombre
                # Insertar test en Moodle si no existe
                if eTestSilaboSemanal.id_test_moodle == 0:
                    instance_id = self._insert_quiz(nombre, intro, fechadesde, fechahasta, limitetiempo, vecesintento, navegacion, nota_maxima, fecha, detallemodelo_nombre, section)
                    eTestSilaboSemanal.id_test_moodle = instance_id
                    eTestSilaboSemanal.estado_id = 4
                    eTestSilaboSemanal.migrado = True
                    eTestSilaboSemanal.save()
                else:
                    quiz_id = eTestSilaboSemanal.id_test_moodle
                    self._update_quiz(quiz_id, nombre, intro, fechadesde, fechahasta, limitetiempo, vecesintento, navegacion, nota_maxima, fecha, detallemodelo_nombre, section)
                    eTestSilaboSemanal.id_test_moodle = quiz_id
                    eTestSilaboSemanal.estado_id = 4
                    eTestSilaboSemanal.migrado = True
                    eTestSilaboSemanal.save()

                return True, "Recurso migrado a Moodle"
            except Exception as ex:
                transaction.set_rollback(True, using=self.connection_eva)
                return False, f"{str(ex)} - {sys.exc_info()[-1].tb_lineno}"
            finally:
                self.cursor.close()

    def migrar_foro(self, eForoSilaboSemanal:ForoSilaboSemanal):
        self.actualizar_html()
        with (transaction.atomic(using=self.connection_eva)):
            try:
                section = self._get_section(CategoriasMoodle.FOROS)
                intro = f"""
                    <div>
                        <h3 class="section-title" style="color: #3b5998;font-weight: bold;">Objetivo:</h3>
                        <p>{eForoSilaboSemanal.objetivo}</p>
                    </div>
                    <div>
                        <h3 class="section-title" style="color: #3b5998;font-weight: bold;">Instrucciones:</h3>
                        <p>{eForoSilaboSemanal.instruccion}</p>
                    </div>
                    <div>
                        <h3 class="section-title" style="color: #3b5998;font-weight: bold;">Recomendaciones:</h3>
                        <p>{eForoSilaboSemanal.recomendacion}</p>
                    </div>
                """

                if eForoSilaboSemanal.rubrica or eForoSilaboSemanal.archivorubrica or eForoSilaboSemanal.archivoforo:
                    if eForoSilaboSemanal.rubrica:
                        intro += f"""
                            <div>
                                <h3 class="section-title" style="color: #3b5998;font-weight: bold;">Rúbrica:</h3>
                                <p>{eForoSilaboSemanal.rubrica}</p>
                            </div>
                            """
                    if eForoSilaboSemanal.archivorubrica:
                        intro += f"""
                            <div class="">
                                <a target="_blank" href="https://sga.itb.edu.ec{eForoSilaboSemanal.archivorubrica.url}">Archivo de rúbrica ({eForoSilaboSemanal.archivorubrica.name.split("/")[-1]})</a>
                            </div>"""
                    if eForoSilaboSemanal.archivoforo:
                        intro += f"""
                            <div>
                                <h3 class="section-title" style="color: #3b5998;font-weight: bold;">Archivos adicionales:</h3>
                                <div class="">
                                    <a target="_blank" href="https://sga.itb.edu.ec{eForoSilaboSemanal.archivoforo.url}">Descargar archivo</a>
                                </div>  
                            </div>
                            """
                intro = intro.replace("'", "''")
                fecha = int(time.mktime(datetime.now().timetuple()))
                horadesde = eForoSilaboSemanal.desde.hour if eForoSilaboSemanal.desde else 0
                minutodesde = eForoSilaboSemanal.desde.minute if eForoSilaboSemanal.desde else 0
                horahasta = eForoSilaboSemanal.hasta.hour if eForoSilaboSemanal.hasta else 23
                minutohasta = eForoSilaboSemanal.hasta.minute if eForoSilaboSemanal.hasta else 59


                fechadesde = datetime(
                    eForoSilaboSemanal.desde.year,
                    eForoSilaboSemanal.desde.month,
                    eForoSilaboSemanal.desde.day,
                    horadesde,
                    minutodesde
                )
                fechahasta = datetime(
                    eForoSilaboSemanal.hasta.year,
                    eForoSilaboSemanal.hasta.month,
                    eForoSilaboSemanal.hasta.day,
                    horahasta,
                    minutohasta
                )
                fechadesde = int(time.mktime(fechadesde.timetuple()))
                fechahasta = int(time.mktime(fechahasta.timetuple()))
                nota_maxima = eForoSilaboSemanal.detallemodelo.nota_maxima if eForoSilaboSemanal.calificar else 0
                calificar = eForoSilaboSemanal.calificar
                detallemodelo_nombre = eForoSilaboSemanal.detallemodelo.nombre
                nombre = "%s" % eForoSilaboSemanal.nombre.replace("'", "")[:252]
                # Insertar Foro en Moodle si no existe
                if eForoSilaboSemanal.id_foro_moodle == 0:
                    instance_id = self._insert_foro(nombre, eForoSilaboSemanal.tipoforo, eForoSilaboSemanal.tipoconsolidacion, fechadesde, fechahasta, nota_maxima, calificar, intro, fecha, detallemodelo_nombre, section)
                    eForoSilaboSemanal.id_foro_moodle = instance_id
                    eForoSilaboSemanal.estado_id = 4
                    eForoSilaboSemanal.migrado = True
                    eForoSilaboSemanal.save()
                else:
                    foro_id = eForoSilaboSemanal.id_foro_moodle
                    self._update_foro(foro_id, nombre, eForoSilaboSemanal.tipoforo, eForoSilaboSemanal.tipoconsolidacion, fechadesde, fechahasta, nota_maxima, calificar, intro, fecha, detallemodelo_nombre, section)
                    eForoSilaboSemanal.id_foro_moodle = foro_id
                    eForoSilaboSemanal.estado_id = 4
                    eForoSilaboSemanal.migrado = True
                    eForoSilaboSemanal.save()

                return True, "Recurso migrado a Moodle"
            except Exception as ex:
                transaction.set_rollback(True, using=self.connection_eva)
                return False, f"{str(ex)} - {sys.exc_info()[-1].tb_lineno}"
            finally:
                self.cursor.close()

    def migrar_tarea(self, eTareaSilaboSemanal:TareaSilaboSemanal):
        self.actualizar_html()
        with ((transaction.atomic(using=self.connection_eva))):
            try:
                section = None
                if eTareaSilaboSemanal.tiporecurso in [1,2]:
                    section = self._get_section(CategoriasMoodle.ACTIVIDAD_CONTACTO_DOCENTE)
                elif eTareaSilaboSemanal.tiporecurso == 3:
                    section = self._get_section(CategoriasMoodle.ACTIVIDAD_AUTONOMA)
                if section is None:
                    raise NameError(u"No se encontro categoria")
                intro = f"""
                    <div>
                        <h3 class="section-title" style="color: #3b5998;font-weight: bold;">Objetivo:</h3>
                        <p>{eTareaSilaboSemanal.objetivo}</p>
                    </div>
                    <div>
                        <h3 class="section-title" style="color: #3b5998;font-weight: bold;">Instrucciones:</h3>
                        <p>{eTareaSilaboSemanal.instruccion}</p>
                    </div>
                    <div>
                        <h3 class="section-title" style="color: #3b5998;font-weight: bold;">Recomendaciones:</h3>
                        <p>{eTareaSilaboSemanal.recomendacion}</p>
                    </div>
                """

                if eTareaSilaboSemanal.rubrica or eTareaSilaboSemanal.archivorubrica or eTareaSilaboSemanal.archivotareasilabo:
                    if eTareaSilaboSemanal.rubrica:
                        intro += f"""
                            <div>
                                <h3 class="section-title" style="color: #3b5998;font-weight: bold;">Rúbrica:</h3>
                                <p>{eTareaSilaboSemanal.rubrica}</p>
                            </div>
                            
                            """
                    if eTareaSilaboSemanal.archivorubrica:
                        intro += f"""
                            <div class="">
                                <a target="_blank" href="https://sga.itb.edu.ec{eTareaSilaboSemanal.archivorubrica.url}">Archivo de rúbrica</a>
                            </div>"""
                    if eTareaSilaboSemanal.archivotareasilabo:
                        intro += f"""
                            <div>
                                <h3 class="section-title" style="color: #3b5998;font-weight: bold;">Archivos adicionales:</h3>
                                <div class="">
                                    <a target="_blank" href="https://sga.itb.edu.ec{eTareaSilaboSemanal.archivotareasilabo.url}">Descargar archivo</a>
                                </div>
                            </div>
                            """
                intro = intro.replace("'", "''")
                fecha = int(time.mktime(datetime.now().timetuple()))
                horadesde = eTareaSilaboSemanal.desde.hour if eTareaSilaboSemanal.desde else 0
                minutodesde = eTareaSilaboSemanal.desde.minute if eTareaSilaboSemanal.desde else 0
                horahasta = eTareaSilaboSemanal.hasta.hour if eTareaSilaboSemanal.hasta else 23
                minutohasta = eTareaSilaboSemanal.hasta.minute if eTareaSilaboSemanal.hasta else 59

                fechadesde = datetime(
                    eTareaSilaboSemanal.desde.year,
                    eTareaSilaboSemanal.desde.month,
                    eTareaSilaboSemanal.desde.day,
                    horadesde,
                    minutodesde
                )
                fechahasta = datetime(
                    eTareaSilaboSemanal.hasta.year,
                    eTareaSilaboSemanal.hasta.month,
                    eTareaSilaboSemanal.hasta.day,
                    horahasta,
                    minutohasta
                )
                fechadesde = int(time.mktime(fechadesde.timetuple()))
                fechahasta = int(time.mktime(fechahasta.timetuple()))
                nota_maxima = eTareaSilaboSemanal.detallemodelo.nota_maxima if eTareaSilaboSemanal.calificar else 0
                calificar = eTareaSilaboSemanal.calificar
                detallemodelo_nombre = eTareaSilaboSemanal.detallemodelo.nombre
                nombre = "%s" % eTareaSilaboSemanal.nombre.replace("'", "")[:252]

                # Insertar Foro en Moodle si no existe
                if eTareaSilaboSemanal.id_tarea_moodle == 0:
                    instance_id = self._insert_tarea(ElementosMoodle.ASSIGN_ID, nombre, intro, fechahasta, fechadesde, eTareaSilaboSemanal.todos, nota_maxima, calificar, detallemodelo_nombre, fecha, section)
                    eTareaSilaboSemanal.id_tarea_moodle = instance_id
                    eTareaSilaboSemanal.estado_id = 4
                    eTareaSilaboSemanal.migrado = True
                    eTareaSilaboSemanal.save()
                else:
                    id_tarea = eTareaSilaboSemanal.id_tarea_moodle
                    self._update_tarea(id_tarea, ElementosMoodle.ASSIGN_ID, nombre, intro, fechahasta, fechadesde, eTareaSilaboSemanal.todos, nota_maxima, calificar, detallemodelo_nombre, fecha, section)
                    eTareaSilaboSemanal.estado_id = id_tarea
                    eTareaSilaboSemanal.estado_id = 4
                    eTareaSilaboSemanal.migrado = True
                    eTareaSilaboSemanal.save()

                return True, "Recurso migrado a Moodle"
            except Exception as ex:
                transaction.set_rollback(True, using=self.connection_eva)
                return False, f"{str(ex)} - {sys.exc_info()[-1].tb_lineno}"
            finally:
                self.cursor.close()

    def _get_section(self, section_mooc):
        self.cursor.execute(
            f"SELECT id FROM {self.prefix}course_sections WHERE course=%s AND section=%s",
            [self.id_moodle_course, section_mooc]
        )
        section = self.cursor.fetchone()

        if not section:
            raise ValueError("La configuración de secciones de Moodle es diferente a la establecida")

        return section[0]

    def _insert_url(self, section, intro, url, fecha, nombre):
        self.cursor.execute(
            f"""INSERT INTO {self.prefix}url (name, externalurl, display, course, intro, introformat, 
            parameters, displayoptions, timemodified) 
             VALUES (%s, %s, '0', %s, %s, '5', 'a:0:{{}}', 'a:1:{{s:10:"printintro";i:1;}}', %s)""",
            [
                nombre,
                url,
                self.id_moodle_course,
                intro,
                fecha
            ]
        )

        self.cursor.execute(
            f"""SELECT id FROM {self.prefix}url WHERE course=%s AND name=%s AND timemodified=%s""",
            [
                self.id_moodle_course,
                nombre,
                fecha
            ]
        )
        instance = self.cursor.fetchone()[0]

        self.cursor.execute(
            f"""INSERT INTO {self.prefix}course_modules (course, module, instance, visible, visibleold, 
            visibleoncoursepage, idnumber, groupmode, groupingid, completion, 
            completiongradeitemnumber, completionview, completionexpected, availability, 
            showdescription, added, section)
            VALUES (%s, %s, %s, '1', '1', '1', '', '0', '0', '2',
            NULL, '1', '0', NULL, '0', %s, %s)""",
            [self.id_moodle_course, ElementosMoodle.URL_ID, instance, fecha, section]
        )

        return self._finalize_moodle_entry(instance, section, fecha)

    def _update_url(self, instance_id, nombre, intro, url, fecha):
        self.cursor.execute(
            f"""SELECT instance FROM {self.prefix}course_modules WHERE course=%s AND id=%s""",
            [
                self.id_moodle_course,
                instance_id
            ]

        )
        instance = self.cursor.fetchone()[0]

        self.cursor.execute(
            f"""UPDATE {self.prefix}url 
            SET name=%s, externalurl=%s, intro=%s, timemodified=%s 
            WHERE course=%s AND id=%s""",
            [
                nombre,
                url,
                intro,
                fecha,
                self.id_moodle_course,
                instance
            ]
        )

        self._update_cache(fecha)

    def _insert_quiz(self, nombre, intro, fechadesde, fechahasta, limitetiempo, vecesintento, navegacion, nota_maxima, fecha, detallemodelo, section):
        # Inserción del quiz en la tabla quiz
        sql_insert_quiz = f"""
            INSERT INTO {self.prefix}quiz (name, timeopen, timeclose, timelimit, overduehandling, graceperiod, 
            grade, attempts, grademethod, questionsperpage, navmethod, shuffleanswers, preferredbehaviour, 
            canredoquestions, attemptonlast, showuserpicture, decimalpoints, questiondecimalpoints, 
            showblocks, subnet, delay1, delay2, browsersecurity, allowofflineattempts, 
            completionattemptsexhausted, course, intro, introformat, timemodified, password, 
            reviewattempt, reviewcorrectness, reviewmarks, reviewspecificfeedback, reviewgeneralfeedback, 
            reviewrightanswer, reviewoverallfeedback) 
            VALUES(%s,%s,%s,%s,'autosubmit','0',%s,%s,'1','1',%s,'1','deferredfeedback','0','0','0','2','-1','0','','0','0','-','0','0',%s,%s,'5',%s,'','65552','16','16','16','16','0','16') 
        """
        self.cursor.execute(sql_insert_quiz,
                            [
                                nombre,
                                fechadesde,
                                fechahasta,
                                limitetiempo,
                                nota_maxima,
                                vecesintento,
                                navegacion,
                                self.id_moodle_course,
                                intro,
                                fecha
                            ]
                            )
        quiz_id = self.cursor.lastrowid

        # Inserción en la tabla course_modules
        sql_insert_course_module = f"""
            INSERT INTO {self.prefix}course_modules 
            (course, module, instance, visible, visibleold, visibleoncoursepage, idnumber, groupmode, groupingid, completion, 
             completiongradeitemnumber, completionview, completionexpected, availability, showdescription, added)
            VALUES (%s, %s, %s, '1', '1', '1', '', '0', '0', '2', '0', '0', '0', NULL, '1', %s)
        """
        self.cursor.execute(sql_insert_course_module,
                            [
                                self.id_moodle_course,
                                ElementosMoodle.QUIZ_ID,
                                quiz_id,
                                fecha
                            ]
                            )
        course_module_id = self.cursor.lastrowid

        # Actualización del cache
        self._update_cache(fecha)

        # Inserción en la tabla quiz_sections
        sql_insert_quiz_sections = f"""INSERT INTO {self.prefix}quiz_sections (quizid, firstslot, heading, shufflequestions) VALUES (%s, '1', '', '0')"""
        self.cursor.execute(sql_insert_quiz_sections, [quiz_id])
        quiz_section_id = self.cursor.lastrowid

        # Inserción en la tabla context
        sql_insert_context = f"""INSERT INTO {self.prefix}context (contextlevel, instanceid, depth, path, locked) VALUES (70, %s, 0, NULL, 0)"""
        self.cursor.execute(sql_insert_context, [course_module_id])
        context_id = self.cursor.lastrowid

        # Actualización del path y depth en {self.prefix}context
        sql_select_context_path = f"""SELECT path FROM {self.prefix}context WHERE contextlevel=50 AND instanceid=%s"""
        self.cursor.execute(sql_select_context_path, [self.id_moodle_course])
        pathcontext = self.cursor.fetchone()[0]
        depthcontext = len(pathcontext.split("/"))
        pathcontext = f"{pathcontext}/{context_id}"

        sql_update_context = f"""
            UPDATE {self.prefix}context 
            SET path=%s, depth=%s 
            WHERE contextlevel=70 AND instanceid=%s
        """
        self.cursor.execute(sql_update_context, [pathcontext, depthcontext, course_module_id])

        # Borrar cualquier feedback anterior para este quiz
        sql_delete_quiz_feedback = f"""DELETE FROM {self.prefix}quiz_feedback WHERE quizid=%s"""
        self.cursor.execute(sql_delete_quiz_feedback, [quiz_id])

        # Inserción de feedback por defecto en quiz_feedback
        sql_insert_quiz_feedback = f"""INSERT INTO {self.prefix}quiz_feedback (quizid, feedbacktext, feedbacktextformat, mingrade, maxgrade) VALUES (%s, '', 1, 0, 11)"""
        self.cursor.execute(sql_insert_quiz_feedback, [quiz_id])

        # Inserción de eventos de apertura y cierre en {self.prefix}event
        descripcion = f"<div class=\"no-overflow\"><p>{intro}</p></div>"
        descripcion = descripcion.replace("'", "''")

        eventos = [
            {"name": f"{nombre} abre", "type": '0', "timestart": fechadesde, "timeduration": fechahasta, "eventtype": 'open'},
            {"name": f"{nombre} cierra", "type": '1', "timestart": fechadesde, "timeduration": fechahasta, "eventtype": 'close'}
        ]

        for evento in eventos:
            sql_insert_event = f"""
                INSERT INTO {self.prefix}event 
                (type, description, courseid, groupid, userid, modulename, instance, timestart, timeduration, timesort, visible, eventtype, priority, name, format, timemodified)
                VALUES (%s, %s, %s, '0', %s, 'quiz', %s, %s, '0', %s, '1', %s, NULL, %s, '1', %s)
            """
            self.cursor.execute(sql_insert_event,
                                [
                                    evento["type"],
                                    descripcion,
                                    self.id_moodle_course,
                                    self.id_moodle_user,
                                    quiz_id,
                                    evento["timestart"],
                                    evento["timeduration"],
                                    evento["eventtype"],
                                    evento["name"],
                                    fecha
                                ]
                                )

        # Verificación o creación de la categoría de calificación
        sql_select_category_id = f"""SELECT id FROM {self.prefix}grade_categories WHERE courseid=%s AND fullname=%s AND depth=2"""
        self.cursor.execute(sql_select_category_id, [self.id_moodle_course, detallemodelo])
        category_id = self.cursor.fetchone()[0]
        if not category_id:
            crear_actualizar_categoria_notas_curso(self.eMateria)
            self.cursor.execute(sql_select_category_id, [self.id_moodle_course, detallemodelo])

        # Inserción en grade_items
        sql_insert_grade_item = f"""
            INSERT INTO {self.prefix}grade_items 
            (courseid, categoryid, itemname, itemtype, itemmodule, iteminstance, itemnumber, gradetype, grademax, grademin, gradepass, timemodified, hidden) 
            VALUES (%s, %s, %s, 'mod', 'quiz', %s, 0, 1, %s, 0, %s, %s, 0)
        """
        self.cursor.execute(sql_insert_grade_item,
                            [
                                self.id_moodle_course,
                                category_id,
                                nombre,
                                quiz_id,
                                nota_maxima,
                                nota_maxima,
                                fecha
                            ]
                            )
        grade_item_id = self.cursor.lastrowid

        sql_insert_grade_item_history = f"""
            INSERT INTO {self.prefix}grade_items_history 
            (courseid, categoryid, itemname, itemtype, itemmodule, iteminstance, itemnumber, iteminfo, idnumber, calculation, gradetype, grademax, grademin, scaleid, outcomeid, gradepass, multfactor, plusfactor, aggregationcoef, aggregationcoef2, sortorder, display, decimals, locked, locktime, needsupdate, weightoverride, timemodified, hidden, action, oldid, source, loggeduser) 
            VALUES (%s, %s, %s, 'mod', 'quiz', %s, 0, NULL, '', NULL, 1, %s, 0, NULL, NULL, %s, 1.00000, 0.00000, 0.00000, 0.00000, 11, 0, NULL, 0, 0, 0, 0, %s, %s, 1, %s, NULL, %s)
        """
        self.cursor.execute(sql_insert_grade_item_history,
                            [
                                self.id_moodle_course,
                                category_id,
                                nombre,
                                quiz_id,
                                nota_maxima,
                                nota_maxima,
                                fecha,
                                fecha,
                                grade_item_id,
                                self.id_moodle_user
                            ]
                            )

        # Actualizar la seccion en course_modules
        sql_update_course_module = f"""UPDATE {self.prefix}course_modules SET section=%s WHERE course=%s AND module=%s AND instance=%s"""
        self.cursor.execute(sql_update_course_module,
                            [
                                section,
                                self.id_moodle_course,
                                ElementosMoodle.QUIZ_ID,
                                quiz_id
                            ]
                            )
        if self.db_vendor == 'postgresql':
            sql_select_course_modules = f"""
                SELECT array_to_string(array_agg(id), ',') 
                FROM {self.prefix}course_modules 
                WHERE deletioninprogress=0 AND course=%s AND section=%s
            """
        elif self.db_vendor == 'mysql':
            sql_select_course_modules = f"""
                    SELECT GROUP_CONCAT(id SEPARATOR ',')
                    FROM {self.prefix}course_modules
                    WHERE deletioninprogress=0 AND course=%s AND section=%s
                    """
        else:
            raise NotImplementedError("Unsupported database type")
        self.cursor.execute(sql_select_course_modules, [self.id_moodle_course, section])
        course_modules = self.cursor.fetchone()[0]

        # Actualizar la secuencia en course_sections
        sql_update_section = f"""UPDATE {self.prefix}course_sections SET sequence=%s WHERE id=%s"""
        self.cursor.execute(sql_update_section, [course_modules, section])

        self._update_cache(fecha)

        return quiz_id

    def _update_quiz(self, quiz_id, nombre, intro, fechadesde, fechahasta, limitetiempo, vecesintento, navegacion, nota_maxima, fecha, detallemodelo, section):
        # Actualización en quiz
        sql_update_quiz = f"""
                UPDATE {self.prefix}quiz 
                SET name=%s, timeopen=%s, timeclose=%s, timelimit=%s, 
                    grade=%s, attempts=%s, navmethod=%s, intro=%s, timemodified=%s 
                WHERE id=%s AND course=%s
            """
        self.cursor.execute(sql_update_quiz,
                            [
                                nombre,
                                fechadesde,
                                fechahasta,
                                limitetiempo,
                                nota_maxima,
                                vecesintento,
                                navegacion,
                                intro,
                                fecha,
                                quiz_id,
                                self.id_moodle_course
                            ]
                            )

        # Obteniendo course_modules
        sql_course_modules = f"""SELECT id FROM {self.prefix}course_modules WHERE course=%s AND module=%s AND instance=%s"""
        self.cursor.execute(sql_course_modules,
                            [
                                self.id_moodle_course,
                                ElementosMoodle.QUIZ_ID,
                                quiz_id
                            ]
                            )
        course_modules = self.cursor.fetchone()[0]

        self._update_cache(fecha)

        # Manejo del contexto
        sql_select_context = f"""SELECT id FROM {self.prefix}context WHERE contextlevel=70 AND instanceid=%s"""
        self.cursor.execute(sql_select_context, [course_modules])
        context_id = self.cursor.fetchone()[0]

        if not context_id:
            sql_insert_context = f"""INSERT INTO {self.prefix}context (contextlevel, instanceid, depth, path, locked) VALUES (70, %s, 0, NULL, 0)"""
            self.cursor.execute(sql_insert_context, [course_modules])
            context_id = self.cursor.lastrowid


        # Actualización del path y depth en context
        sql_get_context_path = f"""SELECT path FROM {self.prefix}context WHERE contextlevel=50 AND instanceid=%s"""
        self.cursor.execute(sql_get_context_path, [self.id_moodle_course])
        pathcontext = self.cursor.fetchone()[0]
        depthcontext = len(pathcontext.split("/"))
        pathcontext = f"{pathcontext}/{context_id}"

        sql_update_context = f"""UPDATE {self.prefix}context SET path=%s, depth=%s WHERE contextlevel=70 AND instanceid=%s"""
        self.cursor.execute(sql_update_context, [pathcontext, depthcontext, course_modules])

        # Actualización en event para 'open' y 'close'
        descripcion = f"<div class=\"no-overflow\"><p>{intro}</p></div>"
        descripcion = descripcion.replace("'", "''")

        eventos = [
            {"name": f"{nombre} abre", "type": '0', "timestart": fechadesde, "timeduration": fechahasta, "eventtype": 'open'},
            {"name": f"{nombre} cierra", "type": '1', "timestart": fechadesde, "timeduration": fechahasta, "eventtype": 'close'}
        ]

        for evento in eventos:
            sql_update_event = f"""
                UPDATE {self.prefix}event 
                SET description=%s, userid=%s, timestart=%s, timeduration=%s, name=%s, timemodified=%s 
                WHERE courseid=%s AND instance=%s AND eventtype=%s
            """
            self.cursor.execute(sql_update_event,
                                [
                                    descripcion,
                                    self.id_moodle_user,
                                    evento["timestart"],
                                    evento["timeduration"],
                                    evento["name"],
                                    fecha,
                                    self.id_moodle_course,
                                    quiz_id,
                                    evento["eventtype"],
                                ]
                                )

        # Manejo de grade_categories
        sql_grade_categories = f"""SELECT id FROM {self.prefix}grade_categories WHERE courseid=%s AND fullname=%s AND depth='2'"""
        self.cursor.execute(sql_grade_categories, [self.id_moodle_course, detallemodelo])
        category_id = self.cursor.fetchone()[0]
        # Creación de categoría si no existe
        if not category_id:
            crear_actualizar_categoria_notas_curso(self.eMateria)
            self.cursor.execute(sql_grade_categories, [self.id_moodle_course, detallemodelo])
            category_id = self.cursor.fetchone()[0]

        # Actualización en grade_items
        sql_grade_items = f"""SELECT id, categoryid FROM {self.prefix}grade_items WHERE courseid=%s AND iteminstance=%s"""
        self.cursor.execute(sql_grade_items, [self.id_moodle_course, quiz_id])
        id_update, category_id_compara = self.cursor.fetchone()

        if category_id != category_id_compara:
            sql_update_grade_items = f"""UPDATE {self.prefix}grade_items SET categoryid=%s WHERE id=%s"""
            self.cursor.execute(sql_update_grade_items, [category_id, id_update])

        # Actualización de las notas
        sql_update_grade_items = f"""
            UPDATE {self.prefix}grade_items 
            SET itemname=%s, grademax=%s, timecreated=%s, timemodified=%s, hidden=%s, gradepass=%s 
            WHERE courseid=%s AND categoryid=%s AND itemtype='mod' AND itemmodule='quiz' AND iteminstance=%s
        """
        self.cursor.execute(sql_update_grade_items,
                            [
                                nombre,
                                nota_maxima,
                                fecha,
                                fecha,
                                fecha,
                                nota_maxima,
                                self.id_moodle_course,
                                category_id,
                                quiz_id
                            ])

        # Obtener grade_items
        sql_get_grade_items = f"""SELECT id FROM {self.prefix}grade_items WHERE courseid=%s AND categoryid=%s AND itemname=%s AND iteminstance=%s"""
        self.cursor.execute(sql_get_grade_items, [self.id_moodle_course, category_id, nombre, quiz_id])
        grade_items = self.cursor.fetchone()[0]

        # Actualización de la secuencia en course_sections
        if self.db_vendor == 'postgresql':
            sql_select_course_modules = f"""
                SELECT array_to_string(array_agg(id), ',') 
                FROM {self.prefix}course_modules 
                WHERE deletioninprogress=0 AND course=%s AND section=%s
            """
        elif self.db_vendor == 'mysql':
            sql_select_course_modules = f"""
                    SELECT GROUP_CONCAT(id SEPARATOR ',')
                    FROM {self.prefix}course_modules
                    WHERE deletioninprogress=0 AND course=%s AND section=%s
                    """
        else:
            raise NotImplementedError("Unsupported database type")
        self.cursor.execute(sql_select_course_modules, [self.id_moodle_course, section])
        course_modules = self.cursor.fetchone()[0]

        # Actualizar la secuencia en course_sections
        sql_update_section = f"""UPDATE {self.prefix}course_sections SET sequence=%s WHERE id=%s"""
        self.cursor.execute(sql_update_section, [course_modules, section])

        # Actualizar la seccion en course_modules
        sql_update_course_module = f"""UPDATE {self.prefix}course_modules SET section=%s WHERE course=%s AND module=%s AND instance=%s"""
        self.cursor.execute(sql_update_course_module,
                            [
                                section,
                                self.id_moodle_course,
                                ElementosMoodle.QUIZ_ID,
                                quiz_id
                            ]
                            )

        self._update_cache(fecha)

    def _insert_foro(self, nombre, tipoforo, tipoconsolidacion, fechadesde, fechahasta, nota_maxima, calificar, intro, fecha, detallemodelo, section):
        # Determinar el tipo de foro
        foro_types = {1: 'qanda', 2: 'single', 3: 'eachuser'}
        foro_type = foro_types.get(tipoforo, '')

        # Determinar el tipo de consolidación
        consolidation_types = {1: '1', 3: '2'}
        assessed = consolidation_types.get(tipoconsolidacion, '0')

        # Insertar el foro en la tabla forum
        sql_insert_forum = f"""
                INSERT INTO {self.prefix}forum 
                (name, type, duedate, cutoffdate, maxbytes, maxattachments, displaywordcount, forcesubscribe, 
                trackingtype, blockperiod, blockafter, warnafter, grade_forum, assessed, scale, assesstimestart, 
                assesstimefinish, completionposts, completiondiscussions, completionreplies, course, intro, 
                introformat, timemodified)
                VALUES (%s, %s, %s, %s, 512000, 9, 0, 0, 1, 0, 0, 0, 0, %s, %s, 0, 0, 1, 0, 0, %s, %s, 5, %s)
            """
        self.cursor.execute(sql_insert_forum, [nombre, foro_type, fechahasta, fechahasta, assessed, nota_maxima,
                                               self.id_moodle_course, intro, fecha
                                               ])
        foro_id = self.cursor.lastrowid

        # Si el tipo de foro es 'single', insertar una discusión y un post inicial
        if foro_type == 'single':
            sql_insert_forum_discussions = f"""
                        INSERT INTO {self.prefix}forum_discussions 
                        (course, forum, name, assessed, groupid, firstpost, timemodified, usermodified, userid) 
                        VALUES (%s, %s, %s, 0, -1, 0, %s, %s, %s)
                    """
            self.cursor.execute(sql_insert_forum_discussions, [
                self.id_moodle_course, foro_id, nombre, fecha, self.id_moodle_user, self.id_moodle_user
            ])
            forum_discussion_id = self.cursor.lastrowid

            sql_insert_forum_posts = f"""
                        INSERT INTO {self.prefix}forum_posts 
                        (discussion, parent, privatereplyto, userid, created, modified, mailed, subject, message, 
                        messageformat, messagetrust, mailnow, wordcount, charcount) 
                        VALUES (%s, 0, 0, %s, %s, %s, 0, %s, %s, 1, 0, 0, 474, 2473)
                    """
            self.cursor.execute(sql_insert_forum_posts, [
                forum_discussion_id, self.id_moodle_user, fecha, fecha, nombre, intro
            ])
            forum_post_id = self.cursor.lastrowid

            sql_update_forum_discussions = f"""
                        UPDATE {self.prefix}forum_discussions 
                        SET firstpost = %s 
                        WHERE id = %s
                    """
            self.cursor.execute(sql_update_forum_discussions, [forum_post_id, forum_discussion_id])

        # Insertar en course_modules
        sql_insert_course_modules = f"""
                INSERT INTO {self.prefix}course_modules 
                (course, module, instance, visible, visibleold, visibleoncoursepage, idnumber, groupmode, 
                groupingid, completion, completiongradeitemnumber, completionview, completionexpected, 
                availability, showdescription, added, section)
                VALUES (%s, %s, %s, '1', '1', '1', '', '0', '0', '2', NULL, '0', '0', NULL, '0', %s, %s)
            """
        self.cursor.execute(sql_insert_course_modules, [
            self.id_moodle_course, ElementosMoodle.FORUM_ID, foro_id, fecha, section
        ])
        course_module_id = self.cursor.lastrowid

        # Insertar en context
        sql_insert_context = f"""
                INSERT INTO {self.prefix}context 
                (contextlevel, instanceid, depth, path, locked) 
                VALUES ('70', %s, '0', NULL, '0')
            """
        self.cursor.execute(sql_insert_context, [course_module_id])
        context_id = self.cursor.lastrowid

        # Obtener el path del contexto del curso
        sql_get_course_context_path = f"""
                SELECT path 
                FROM {self.prefix}context 
                WHERE contextlevel = 50 AND instanceid = %s
            """
        self.cursor.execute(sql_get_course_context_path, [self.id_moodle_course])
        pathcontext = self.cursor.fetchone()[0]
        depthcontext = len(pathcontext.split("/"))
        pathcontext = f"{pathcontext}/{context_id}"

        sql_update_context = f"""
                UPDATE {self.prefix}context 
                SET path = %s, depth = %s 
                WHERE contextlevel = 70 AND instanceid = %s
            """
        self.cursor.execute(sql_update_context, [pathcontext, depthcontext, course_module_id])

        # Insertar en event
        sql_insert_event = f"""
                INSERT INTO {self.prefix}event 
                (modulename, courseid, groupid, userid, instance, type, description, name, eventtype, 
                timestart, timesort, format, timemodified) 
                VALUES ('forum', %s, '0', %s, %s, '1', %s, %s, 'due', %s, %s, '1', %s)
            """
        self.cursor.execute(sql_insert_event, [
            self.id_moodle_course, self.id_moodle_user, foro_id, intro, nombre,
            fechadesde, fechadesde, fecha
        ])

        # Obtener o insertar en grade_categories y grade_items si es necesario
        if calificar:
            sql_get_category_id = f"""
                    SELECT id 
                    FROM {self.prefix}grade_categories 
                    WHERE courseid = %s AND fullname = %s AND depth = '2'
                """
            self.cursor.execute(sql_get_category_id, [self.id_moodle_course, detallemodelo])
        else:
            sql_get_category_id = f"""
                    SELECT id 
                    FROM {self.prefix}grade_categories 
                    WHERE courseid = %s AND fullname = '?' AND depth = '1'
                """
            self.cursor.execute(sql_get_category_id, [self.id_moodle_course])

        category_id = self.cursor.fetchone()[0]

        if calificar:
            sql_insert_grade_item = f"""
                        INSERT INTO {self.prefix}grade_items 
                        (courseid, categoryid, itemname, itemtype, itemmodule, iteminstance, itemnumber, iteminfo, 
                        idnumber, calculation, gradetype, grademax, grademin, scaleid, outcomeid, gradepass, 
                        multfactor, plusfactor, aggregationcoef, aggregationcoef2, sortorder, display, decimals, 
                        locked, locktime, needsupdate, weightoverride, timecreated, timemodified, hidden)
                        VALUES (%s, %s, %s, 'mod', 'forum', %s, '0', NULL, '', NULL, '1', %s, '0', NULL, NULL, '0', 
                        '1', '0', '0', '0', '8', '0', NULL, '0', '0', '0', '0', %s, %s, '0')
                    """
            self.cursor.execute(sql_insert_grade_item,
                                [
                                    self.id_moodle_course,
                                    category_id,
                                    f"{nombre} calificación".replace("'", "")[:230],
                                    foro_id,
                                    null_to_numeric(nota_maxima, 5) if calificar else 0,
                                    fecha,
                                    fecha
                                ])
            grade_item_id = self.cursor.lastrowid

            # PROCEDEMOS A BUSCAR LA CATEGORIA GRADES raiz
            sql_select_grade_categories = f"""SELECT id FROM {self.prefix}grade_categories WHERE courseid=%s AND fullname='?' and depth='1' """
            self.cursor.execute(sql_select_grade_categories, [self.id_moodle_course])
            category_id_raiz = self.cursor.fetchone()[0]

            sql_insert_grade_items_history = f"""
                INSERT INTO {self.prefix}grade_items_history 
                (courseid, categoryid, itemname, itemtype, itemmodule, iteminstance, itemnumber, iteminfo, idnumber,
                calculation, gradetype, grademax, grademin, scaleid, outcomeid, gradepass, multfactor, plusfactor, 
                aggregationcoef, aggregationcoef2, sortorder, display, decimals, locked, locktime, needsupdate, 
                weightoverride, timemodified, hidden, action, oldid, source, loggeduser) 
                VALUES(%s, %s, %s, 'mod', 'forum', %s, '0', NULL, %s, NULL, '1', %s, '0.00000', NULL, NULL, 
                '0.00000', '1.00000', '0.00000', '0.00000', '0.00000', %s, '0', NULL, '0', '0', '1', '0', %s, '0',
                 '1', %s, NULL, %s)"""
            self.cursor.execute(sql_insert_grade_items_history,
                                [
                                    self.id_moodle_course,
                                    category_id_raiz,
                                    f"{nombre} calificación".replace("'", "")[:230],
                                    foro_id,
                                    course_module_id,
                                    null_to_numeric(nota_maxima, 5) if calificar else 0,
                                    depthcontext,
                                    fecha,
                                    grade_item_id,
                                    self.id_moodle_user
                                ])

        sql_insert_grading_areas = f"""
            INSERT INTO {self.prefix}grading_areas 
            (contextid, component, areaname, activemethod) 
            VALUES(%s, 'mod_forum', 'forum', NULL) """
        self.cursor.execute(sql_insert_grading_areas, [context_id])


        sql_insert_block_recent_activity = f"""
            INSERT INTO {self.prefix}block_recent_activity 
            (action, timecreated, courseid, cmid, userid) 
            VALUES('0', %s, %s, %s, %s) """
        self.cursor.execute(sql_insert_block_recent_activity,
                            [
                                fecha,
                                self.id_moodle_course,
                                course_module_id,
                                self.id_moodle_user
                            ])

        # PROCEDEMOS A BUSCAR sequence
        sql_select_course_sections = f"""SELECT sequence FROM {self.prefix}course_sections WHERE id=%s"""
        self.cursor.execute(sql_select_course_sections, [section])
        sequence = self.cursor.fetchone()[0]
        sql_update_course_sections = f"""UPDATE {self.prefix}course_sections SET sequence = %s WHERE id = %s """
        self.cursor.execute(sql_update_course_sections, ["%s,%s" % (sequence, course_module_id), section])

        self._update_cache(fecha)

        return foro_id

    def _update_foro(self, foro_id, nombre, tipoforo, tipoconsolidacion, fechadesde, fechahasta, nota_maxima, calificar, intro, fecha, detallemodelo, section):
        # Determinar el tipo de foro
        foro_types = {1: 'qanda', 2: 'single', 3: 'eachuser'}
        foro_type = foro_types.get(tipoforo, '')

        # Determinar el tipo de consolidación
        consolidation_types = {1: '1', 3: '2'}
        assessed = consolidation_types.get(tipoconsolidacion, '0')

        self.cursor.execute(
            f"""SELECT id FROM {self.prefix}course_modules WHERE course=%s AND instance=%s""",
            [
                self.id_moodle_course,
                foro_id
            ]

        )
        course_module_id = self.cursor.fetchone()[0]

        sql_update_forum = f"""
                        UPDATE {self.prefix}forum 
                        SET name=%s,
                        type=%s,
                        duedate=%s,
                        cutoffdate=%s,
                        assessed=%s,
                        scale=%s,
                        intro=%s,
                        timemodified=%s
                        WHERE course=%s AND id=%s
                    """
        self.cursor.execute(sql_update_forum,
                            [
                                nombre,
                                foro_type,
                                fechahasta,
                                fechahasta,
                                assessed,
                                nota_maxima,
                                intro,
                                fecha,
                                self.id_moodle_course,
                                foro_id
                            ])

        # Obtener o insertar en grade_categories y grade_items si es necesario
        if calificar:
            sql_get_category_id = f"""
                            SELECT id 
                            FROM {self.prefix}grade_categories 
                            WHERE courseid = %s AND fullname = %s AND depth = '2'
                        """
            self.cursor.execute(sql_get_category_id, [self.id_moodle_course, detallemodelo])
        else:
            sql_get_category_id = f"""
                            SELECT id 
                            FROM {self.prefix}grade_categories 
                            WHERE courseid = %s AND fullname = '?' AND depth = '1'
                        """
            self.cursor.execute(sql_get_category_id, [self.id_moodle_course])

        category_id = self.cursor.fetchone()[0]
        if calificar:
            sql_update_grade_items = f"""
                UPDATE {self.prefix}grade_items SET
                categoryid=%s,
                itemname=%s,
                gradetype=%s,
                grademax=%s,
                timemodified=%s
                WHERE courseid=%s and iteminstance=%s"""
            self.cursor.execute(sql_update_grade_items,
                                [
                                    category_id,
                                    f"{nombre} calificación".replace("'", "")[:230],
                                    '1' if calificar else '3',
                                    null_to_numeric(nota_maxima, 5) if calificar else 0,
                                    fecha,
                                    self.id_moodle_course,
                                    foro_id
                                ])
        self._update_cache(fecha)

    def _insert_tarea(self, elemento_modulo, nombre, intro, fechahasta, fechadesde, todos, nota_maxima, calificar, detallemodelo, fecha, section):
        sql_insert_assign = f"""
            INSERT INTO {self.prefix}assign 
            (name, timemodified, course, intro, introformat, alwaysshowdescription, submissiondrafts, 
            requiresubmissionstatement, sendnotifications, sendlatenotifications, sendstudentnotifications, 
            duedate, cutoffdate, gradingduedate, allowsubmissionsfromdate, grade, completionsubmit, teamsubmission, 
            requireallteammemberssubmit, blindmarking, hidegrader, attemptreopenmethod, maxattempts, 
            preventsubmissionnotingroup, markingworkflow, markingallocation) 
            VALUES(%s, %s, %s, %s, '5', '1', '0', '0', '0', '0', '1', %s, %s, '0', %s, %s, '1', '0', '0', '0', '0', 'none', '-1', '0', '0', '0')"""
        self.cursor.execute(sql_insert_assign,
                            [
                                nombre,
                                fecha,
                                self.id_moodle_course,
                                intro,
                                fechahasta,
                                fechahasta,
                                fechadesde,
                                nota_maxima if calificar else 0
                            ]
                            )
        tarea_id = self.cursor.lastrowid

        sql_insert_course_module = f"""
            INSERT INTO {self.prefix}course_modules 
            (course, module, instance, visible, visibleold, visibleoncoursepage, idnumber, groupmode, groupingid, 
            completion, completiongradeitemnumber, completionview, completionexpected, availability, showdescription, 
            added, section) 
            VALUES(%s, %s, %s, '1', '1', '1', '', '0', '0', '2', NULL, '0', '0', NULL, '0', %s, %s)
            """
        self.cursor.execute(sql_insert_course_module,
                            [
                                self.id_moodle_course,
                                elemento_modulo,
                                tarea_id,
                                fecha,
                                section
                            ]
                            )
        # instanceid
        course_module_id = self.cursor.lastrowid

        sql_get_context = f"""SELECT id FROM {self.prefix}context WHERE contextlevel=70 AND instanceid=%s """
        self.cursor.execute(sql_get_context, [course_module_id])
        context_id = self.cursor.fetchone()

        if not context_id:
            sql_insert_context = f"""INSERT INTO {self.prefix}context (contextlevel, instanceid, depth, path, locked) VALUES('70',%s,'0',NULL,'0')"""
            self.cursor.execute(sql_insert_context, [course_module_id])
            context_id = self.cursor.lastrowid

        # Actualización del path y depth en context
        sql_get_context_path = f"""SELECT path FROM {self.prefix}context WHERE contextlevel=50 AND instanceid=%s"""
        self.cursor.execute(sql_get_context_path, [self.id_moodle_course])
        pathcontext = self.cursor.fetchone()[0]
        depthcontext = len(pathcontext.split("/"))
        pathcontext = f"{pathcontext}/{context_id}"

        sql_update_context = f"""UPDATE {self.prefix}context SET path=%s, depth=%s WHERE contextlevel=70 AND instanceid=%s"""
        self.cursor.execute(sql_update_context, [pathcontext, depthcontext, course_module_id])

        sql_insert_event = f"""
            INSERT INTO {self.prefix}event 
            (modulename, courseid, groupid, userid, instance, type, description, name, eventtype, timestart, timesort, 
            format, timemodified) 
            VALUES('assign', %s, '0', %s,%s, '1',%s,%s,'due', %s,%s,'1',%s)
            """
        self.cursor.execute(sql_insert_event,
                            [
                                self.id_moodle_course,
                                self.id_moodle_user,
                                tarea_id,
                                intro,
                                nombre,
                                fechadesde,
                                fechadesde,
                                fecha
                            ])

        if calificar:
            sql_grade_categories = f"""SELECT id FROM {self.prefix}grade_categories WHERE courseid=%s AND fullname=%s AND depth='2'"""
            self.cursor.execute(sql_grade_categories, [self.id_moodle_course, detallemodelo])
            category_id = self.cursor.fetchone()[0]

            # Creación de categoría si no existe
            if not category_id:
                crear_actualizar_categoria_notas_curso(self.eMateria)
                self.cursor.execute(sql_grade_categories, [self.id_moodle_course, detallemodelo])
                category_id = self.cursor.fetchone()[0]
        else:
            sql_grade_categories = f"""SELECT id FROM {self.prefix}grade_categories WHERE courseid=%s AND fullname='?' AND depth='1'"""
            self.cursor.execute(sql_grade_categories, [self.id_moodle_course])
            category_id = self.cursor.fetchone()[0]

        sql_insert_grade_items = f"""
            INSERT INTO {self.prefix}grade_items 
            (courseid, categoryid, itemname, itemtype, itemmodule, iteminstance, itemnumber, iteminfo, idnumber, 
            calculation, gradetype, grademax, grademin, scaleid, outcomeid, gradepass, multfactor, plusfactor, 
            aggregationcoef, aggregationcoef2, sortorder, display, decimals, locked, locktime, needsupdate, 
            weightoverride, timecreated, timemodified, hidden) 
            VALUES(%s, %s, %s, 'mod','assign',%s, '0', NULL, '', NULL, %s, %s, '0', NULL, NULL, '0', '1', '0', '0', '0', '8', '0', NULL, '0', '0', '0', '0',%s,%s, '0')"""
        self.cursor.execute(sql_insert_grade_items,
                            [
                                self.id_moodle_course,
                                category_id,
                                nombre,
                                course_module_id,
                                '1' if calificar else '3',
                                null_to_numeric(nota_maxima, 5) if calificar else 0,
                                fecha,
                                fecha
                            ])
        grade_item_id = self.cursor.lastrowid

        # PROCEDEMOS A BUSCAR LA CATEGORIA GRADES raiz
        sql_select_grade_categories = f"""SELECT id FROM {self.prefix}grade_categories WHERE courseid=%s AND fullname='?' and depth='1' """
        self.cursor.execute(sql_select_grade_categories, [self.id_moodle_course])
        category_id_raiz = self.cursor.fetchone()[0]


        sql_insert_grade_items_history = f"""
            INSERT INTO {self.prefix}grade_items_history 
            (courseid, categoryid, itemname, itemtype, itemmodule, iteminstance, itemnumber, iteminfo, idnumber, 
            calculation, gradetype, grademax, grademin, scaleid, outcomeid, gradepass, multfactor, plusfactor, 
            aggregationcoef, aggregationcoef2, sortorder, display, decimals, locked, locktime, needsupdate, 
            weightoverride, timemodified, hidden, action, oldid, source, loggeduser) 
            VALUES(%s,%s, %s, 'mod', 'assign', %s, '0', NULL, %s, NULL, %s, %s, '0.00000', NULL, NULL, '0.00000', 
            '1.00000', '0.00000', '0.00000', '0.00000', %s, '0', NULL, '0', '0', '1', '0', %s, '0', '1', %s, NULL, %s) """
        self.cursor.execute(sql_insert_grade_items_history,
                            [
                                self.id_moodle_course,
                                category_id_raiz,
                                nombre,
                                tarea_id,
                                course_module_id,
                                '1' if calificar else '3',
                                null_to_numeric(nota_maxima, 5) if calificar else 0,
                                depthcontext,
                                fecha,
                                grade_item_id,
                                self.id_moodle_user
                            ])

        sql_insert_grade_items_history = f"""
            INSERT INTO {self.prefix}grade_items_history 
            (courseid, categoryid, itemname, itemtype, itemmodule, iteminstance, itemnumber, iteminfo, idnumber, 
            calculation, gradetype, grademax, grademin, scaleid, outcomeid, gradepass, multfactor, plusfactor, 
            aggregationcoef, aggregationcoef2, sortorder, display, decimals, locked, locktime, needsupdate, 
            weightoverride, timemodified, hidden, action, oldid, source, loggeduser) 
            VALUES(%s,%s, %s, 'mod', 'assign', %s, '0', NULL, '', NULL, %s, %s, '0.00000', NULL, NULL, '0.00000', 
            '1.00000', '0.00000', '0.00000', '0.00000', %s, '0', NULL, '0', '0', '1', '0', %s, '0', '2', %s, NULL, %s) """
        self.cursor.execute(sql_insert_grade_items_history,
                            [
                                self.id_moodle_course,
                                category_id,
                                nombre,
                                tarea_id,
                                '1' if calificar else '3',
                                null_to_numeric(nota_maxima, 5) if calificar else 0,
                                depthcontext,
                                fecha,
                                grade_item_id,
                                self.id_moodle_user
                            ])

        sql_insert_grade_items_history = f"""
            INSERT INTO {self.prefix}grade_items_history 
            (courseid, categoryid, itemname, itemtype, itemmodule, iteminstance, itemnumber, iteminfo, idnumber, 
            calculation, gradetype, grademax, grademin, scaleid, outcomeid, gradepass, multfactor, plusfactor, 
            aggregationcoef, aggregationcoef2, sortorder, display, decimals, locked, locktime, needsupdate, 
            weightoverride, timemodified, hidden, action, oldid, source, loggeduser) 
            VALUES(%s,%s, %s, 'mod', 'assign', %s, '0', NULL, '', NULL, %s, %s, '0.00000', NULL, NULL, '0.00000', 
            '1.00000', '0.00000', '0.00000', '0.00000', %s, '0', NULL, '0', '0', '1', '0', %s, '0', '2', %s, NULL, %s) """
        self.cursor.execute(sql_insert_grade_items_history,
                            [
                                self.id_moodle_course,
                                category_id,
                                nombre,
                                tarea_id,
                                '1' if calificar else '3',
                                null_to_numeric(nota_maxima, 5) if calificar else 0,
                                depthcontext,
                                fecha,
                                grade_item_id,
                                self.id_moodle_user
                            ])


        sql_insert_assign_plugin_config = f"""
            INSERT INTO {self.prefix}assign_plugin_config 
            (assignment, subtype, plugin, name, value) 
            VALUES(%s, 'assignsubmission', 'onlinetext', 'enabled', '0') """
        self.cursor.execute(sql_insert_assign_plugin_config, [tarea_id])

        sql_insert_assign_plugin_config = f"""
            INSERT INTO {self.prefix}assign_plugin_config 
            (assignment, subtype, plugin, name, value) 
            VALUES(%s, 'assignsubmission', 'file', 'enabled', '1') """
        self.cursor.execute(sql_insert_assign_plugin_config, [tarea_id])

        sql_insert_assign_plugin_config = f"""
            INSERT INTO {self.prefix}assign_plugin_config 
            (assignment, subtype, plugin, name, value) 
            VALUES(%s, 'assignsubmission', 'file', 'maxfilesubmissions', '20') """
        self.cursor.execute(sql_insert_assign_plugin_config, [tarea_id])

        sql_insert_assign_plugin_config = f"""
            INSERT INTO {self.prefix}assign_plugin_config 
            (assignment, subtype, plugin, name, value) 
            VALUES(%s, 'assignsubmission', 'file', 'maxsubmissionsizebytes', '0') """
        self.cursor.execute(sql_insert_assign_plugin_config, [tarea_id])

        if todos:
            sql_insert_assign_plugin_config = f"""
                INSERT INTO {self.prefix}assign_plugin_config 
                (assignment, subtype, plugin, name, value) 
                VALUES(%s, 'assignsubmission', 'file', 'filetypeslist', '*') """
            self.cursor.execute(sql_insert_assign_plugin_config, [tarea_id])
        else:
            sql_insert_assign_plugin_config = f"""
                INSERT INTO {self.prefix}assign_plugin_config 
                (assignment, subtype, plugin, name, value) 
                VALUES(%s, 'assignsubmission', 'file', 'filetypeslist', 'document,spreadsheet,presentation') """
            self.cursor.execute(sql_insert_assign_plugin_config, [tarea_id])

        sql_insert_assign_plugin_config = f"""
            INSERT INTO {self.prefix}assign_plugin_config 
            (assignment, subtype, plugin, name, value) 
            VALUES(%s, 'assignsubmission', 'comments', 'enabled', '1') """
        self.cursor.execute(sql_insert_assign_plugin_config, [tarea_id])

        sql_insert_assign_plugin_config = f"""
            INSERT INTO {self.prefix}assign_plugin_config 
            (assignment, subtype, plugin, name, value) 
            VALUES(%s, 'assignfeedback', 'comments', 'enabled', '1') """
        self.cursor.execute(sql_insert_assign_plugin_config, [tarea_id])

        sql_insert_assign_plugin_config = f"""
            INSERT INTO {self.prefix}assign_plugin_config 
            (assignment, subtype, plugin, name, value) 
            VALUES(%s, 'assignfeedback', 'comments', 'commentinline', '0') """
        self.cursor.execute(sql_insert_assign_plugin_config, [tarea_id])

        sql_insert_assign_plugin_config = f"""
            INSERT INTO {self.prefix}assign_plugin_config 
            (assignment, subtype, plugin, name, value) 
            VALUES(%s, 'assignfeedback', 'editpdf', 'enabled', '1') """
        self.cursor.execute(sql_insert_assign_plugin_config, [tarea_id])

        sql_insert_assign_plugin_config = f"""
            INSERT INTO {self.prefix}assign_plugin_config 
            (assignment, subtype, plugin, name, value) 
            VALUES(%s, 'assignfeedback', 'offline', 'enabled', '0') """
        self.cursor.execute(sql_insert_assign_plugin_config, [tarea_id])

        sql_insert_assign_plugin_config = f"""
            INSERT INTO {self.prefix}assign_plugin_config 
            (assignment, subtype, plugin, name, value) 
            VALUES(%s, 'assignfeedback', 'file', 'enabled', '0') """
        self.cursor.execute(sql_insert_assign_plugin_config, [tarea_id])

        sql_insert_grading_areas = f"""
            INSERT INTO {self.prefix}grading_areas 
            (contextid, component, areaname, activemethod) 
            VALUES(%s, 'mod_assign', 'submissions', NULL) """
        self.cursor.execute(sql_insert_assign_plugin_config, [context_id])

        sql_insert_block_recent_activity = f"""
            INSERT INTO {self.prefix}block_recent_activity 
            (action, timecreated, courseid, cmid, userid) VALUES('0', %s, %s, %s, %s) """
        self.cursor.execute(sql_insert_block_recent_activity, [fecha, self.id_moodle_course, course_module_id, self.id_moodle_user])

        # PROCEDEMOS A BUSCAR sequence
        sql_select_course_sections = f"""SELECT sequence FROM {self.prefix}course_sections WHERE id=%s"""
        self.cursor.execute(sql_select_course_sections, [section])
        sequence = self.cursor.fetchone()[0]
        sql_update_course_sections = f"""UPDATE {self.prefix}course_sections SET sequence = %s WHERE id = %s """
        self.cursor.execute(sql_update_course_sections, ["%s,%s" % (sequence, course_module_id), section])

        self._update_cache(fecha)

        return tarea_id

    def _update_tarea(self, tarea_id, elemento_modulo, nombre, intro, fechahasta, fechadesde, todos, nota_maxima, calificar, detallemodelo, fecha, section):
        sql_get_course_module = f"""SELECT id FROM {self.prefix}course_modules WHERE course=%s AND instance=%s """
        self.cursor.execute(sql_get_course_module,
                            [
                                self.id_moodle_course,
                                tarea_id
                            ]
                            )
        instance_id = self.cursor.fetchone()[0]
        instance = tarea_id
        sql_get_context = f"""SELECT id FROM {self.prefix}context WHERE contextlevel=70 AND instanceid=%s """
        self.cursor.execute(sql_get_context, [instance_id])
        context_id = self.cursor.fetchone()[0]

        sql_update_assign = f"""
            UPDATE {self.prefix}assign 
            SET name=%s, 
                timemodified=%s, 
                intro=%s, 
                duedate=%s, 
                cutoffdate=%s, 
                allowsubmissionsfromdate=%s, 
                grade=%s
            WHERE id=%s"""
        self.cursor.execute(sql_update_assign, [
            nombre, fecha, intro, fechahasta, fechahasta, fechadesde, nota_maxima if calificar else 0, instance
        ])

        sql_update_assign = f"""
            UPDATE {self.prefix}event 
            SET description=%s,
                name=%s,
                timestart=%s,
                timesort=%s,
                timemodified=%s
            WHERE instance=%s and courseid=%s """
        self.cursor.execute(sql_update_assign, [
            intro, nombre, fechadesde, fechadesde,
            fecha, instance, self.id_moodle_course
        ])

        if todos:
            sql_update_assign_plugin_config = f"""UPDATE {self.prefix}assign_plugin_config SET value = '*' WHERE assignment = %s and name = 'filetypeslist'"""
            self.cursor.execute(sql_update_assign_plugin_config, [instance])

        if calificar:
            sql_grade_categories = f"""SELECT id FROM {self.prefix}grade_categories WHERE courseid=%s AND fullname=%s AND depth='2'"""
            self.cursor.execute(sql_grade_categories, [self.id_moodle_course, detallemodelo])
            category_id = self.cursor.fetchone()[0]

            # Creación de categoría si no existe
            if not category_id:
                crear_actualizar_categoria_notas_curso(self.eMateria)
                self.cursor.execute(sql_grade_categories, [self.id_moodle_course, detallemodelo])
                category_id = self.cursor.fetchone()[0]
        else:
            sql_grade_categories = f"""SELECT id FROM {self.prefix}grade_categories WHERE courseid=%s AND fullname='?' AND depth='1'"""
            self.cursor.execute(sql_grade_categories, [self.id_moodle_course])
            category_id = self.cursor.fetchone()[0]

        sql_update_grade_items = f"""UPDATE {self.prefix}grade_items 
                    SET categoryid=%s,
                        itemname=%s,
                        gradetype=%s,
                        grademax=%s,
                        timemodified=%s
                    WHERE courseid=%s AND iteminstance=%s"""
        self.cursor.execute(sql_update_grade_items, [
            category_id,
            nombre,
            '1' if calificar else '3',
            null_to_numeric(nota_maxima, 5) if calificar else 0,
            fecha, self.id_moodle_course, instance
        ])

        self._update_cache(fecha)


    def _finalize_moodle_entry(self, instance, section, fecha):
        self.cursor.execute(
            f"""SELECT id FROM {self.prefix}course_modules WHERE course=%s AND module=%s AND instance=%s AND section=%s""",
            [self.id_moodle_course, ElementosMoodle.URL_ID, instance, section]
        )
        instance_id = self.cursor.fetchone()[0]

        self.cursor.execute(
            f"""INSERT INTO {self.prefix}context (contextlevel, instanceid, depth, path, locked) VALUES ('70', %s, '0', NULL, '0')""",
            [instance_id]
        )

        self.cursor.execute(
            f"""SELECT id FROM {self.prefix}context WHERE contextlevel=70 AND instanceid=%s""",
            [instance_id]
        )
        context_id = self.cursor.fetchone()[0]

        self.cursor.execute(
            f"""SELECT path FROM {self.prefix}context WHERE contextlevel=50 AND instanceid=%s""",
            [self.id_moodle_course]
        )
        pathcontext = self.cursor.fetchone()[0]
        depthcontext = len(pathcontext.split("/"))
        pathcontext = f"{pathcontext}/{context_id}"

        self.cursor.execute(
            f"""UPDATE {self.prefix}context SET path=%s, depth=%s WHERE contextlevel=70 AND instanceid=%s""",
            [pathcontext, depthcontext, instance_id]
        )

        self.cursor.execute(
            f"""SELECT sequence FROM {self.prefix}course_sections WHERE id=%s""",
            [section]
        )
        sequence = self.cursor.fetchone()[0]
        self.cursor.execute(
            f"""UPDATE {self.prefix}course_sections SET sequence=%s WHERE id=%s""",
            [f"{sequence},{instance_id}", section]
        )

        self._update_cache(fecha)

        return instance_id

    def _update_cache(self, fecha):
        self.cursor.execute(
            f"""UPDATE {self.prefix}course SET cacherev=%s WHERE id=%s""",
            [fecha, self.id_moodle_course]
        )
