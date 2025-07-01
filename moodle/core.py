class CategoriasMoodle:
    # Definición de las constantes
    INTRODUCCION = 0
    CLASES_VIRTUALES = 1
    CLASES_DE_REFUERZO = 2
    ACTIVIDAD_AUTONOMA = 3
    ACTIVIDAD_CONTACTO_DOCENTE = 4
    FOROS = 5
    COMPENDIOS = 6
    PRESENTACIONES = 7
    VIDEOS_MAGISTRALES = 8
    MATERIAL_COMPLEMENTARIO = 9
    GUIAS_DEL_ESTUDIANTE = 10
    ACTIVIDADES_PRACTICA_EXPERIMENTAL = 11
    EXAMENES = 12

    # Mapea los valores a sus descripciones
    @classmethod
    def get_options(cls):
        return [
            (cls.INTRODUCCION, 'Introducción'),
            (cls.CLASES_VIRTUALES, 'Clases virtuales'),
            (cls.CLASES_DE_REFUERZO, 'Clases de refuerzo'),
            (cls.ACTIVIDAD_AUTONOMA, 'Actividad autónoma'),
            (cls.ACTIVIDAD_CONTACTO_DOCENTE, 'Actividad de contacto docente'),
            (cls.FOROS, 'Foros'),
            (cls.COMPENDIOS, 'Compendios'),
            (cls.PRESENTACIONES, 'Presentaciones'),
            (cls.VIDEOS_MAGISTRALES, 'Videos magistrales'),
            (cls.MATERIAL_COMPLEMENTARIO, 'Material complementario'),
            (cls.GUIAS_DEL_ESTUDIANTE, 'Guías del estudiante'),
            (cls.ACTIVIDADES_PRACTICA_EXPERIMENTAL, 'Actividades de práctica experimental'),
            (cls.EXAMENES, 'Exámenes'),
        ]

    @classmethod
    def get_option_display(cls, valor):
        options = cls.get_options()
        return options[valor][1]


class ElementosMoodle:
    # Definición de constantes
    ASSIGN_ID = 1
    ASSIGNMENT_ID = 2
    BOOK_ID = 3
    CHAT_ID = 4
    CHOICE_ID = 5
    DATA_ID = 6
    FEEDBACK_ID = 7
    FOLDER_ID = 8
    FORUM_ID = 9
    GLOSSARY_ID = 10
    IMSCP_ID = 11
    LABEL_ID = 12
    LESSON_ID = 13
    LTI_ID = 14
    PAGE_ID = 15
    QUIZ_ID = 16
    RESOURCE_ID = 17
    SCORM_ID = 18
    SURVEY_ID = 19
    URL_ID = 20
    WIKI_ID = 21
    WORKSHOP_ID = 22
    ZOOM_ID = 23
    HVP_ID = 24
    H5PACTIVITY_ID = 25
    BIGBLUEBUTTONBN_ID = 26
    COURSECERTIFICATE_ID = 27

    @classmethod
    def get_options(cls):
        return [
            (cls.ASSIGN_ID, 'assign'),
            (cls.ASSIGNMENT_ID, 'assignment'),
            (cls.BOOK_ID, 'book'),
            (cls.CHAT_ID, 'chat'),
            (cls.CHOICE_ID, 'choice'),
            (cls.DATA_ID, 'data'),
            (cls.FEEDBACK_ID, 'feedback'),
            (cls.FOLDER_ID, 'folder'),
            (cls.FORUM_ID, 'forum'),
            (cls.GLOSSARY_ID, 'glossary'),
            (cls.IMSCP_ID, 'imscp'),
            (cls.LABEL_ID, 'label'),
            (cls.LESSON_ID, 'lesson'),
            (cls.LTI_ID, 'lti'),
            (cls.PAGE_ID, 'page'),
            (cls.QUIZ_ID, 'quiz'),
            (cls.RESOURCE_ID, 'resource'),
            (cls.SCORM_ID, 'scorm'),
            (cls.SURVEY_ID, 'survey'),
            (cls.URL_ID, 'url'),
            (cls.WIKI_ID, 'wiki'),
            (cls.WORKSHOP_ID, 'workshop'),
            (cls.ZOOM_ID, 'zoom'),
            (cls.HVP_ID, 'hvp'),
            (cls.H5PACTIVITY_ID, 'h5pactivity'),
            (cls.BIGBLUEBUTTONBN_ID, 'bigbluebuttonbn'),
            (cls.COURSECERTIFICATE_ID, 'coursecertificate'),
        ]

    @classmethod
    def get_option_display(cls, valor):
        options = cls.get_options()
        return options[valor][1]
