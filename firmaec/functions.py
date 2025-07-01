import pymupdf  # fitz


def obtener_coordenadas_firma_en_pdf(path_file, palabras_clave):
    """
    Busca la posición (x, y) de una palabra clave en las dos últimas páginas de un documento PDF.

    :param path_file: Ruta del archivo PDF.
    :param palabras_clave: Palabra o frase a buscar en el PDF.
    :return: Coordenadas (x, y) de la palabra clave y el número de la página, o None si no se encuentra.
    """

    def buscar_palabras_en_pagina(page):
        """Busca las palabras en una página y devuelve las coordenadas."""
        words_blocks = page.get_text("blocks")
        for block in words_blocks:
            try:
                # Unimos el texto del bloque para buscar la secuencia completa
                if palabras_clave in block[4].replace('\n', ' '):
                    x = int(block[0])
                    y = 5000 - int(block[3]) - 4125
                    return x, y
            except Exception:
                continue
        return None, None

    # Abrir el documento PDF
    documento = pymupdf.open(path_file)

    # Determinar las páginas donde se buscará la palabra clave
    ultima_pagina = documento.page_count - 1
    penultima_pagina = ultima_pagina - 1

    # Buscar en la última página
    x, y = buscar_palabras_en_pagina(documento[ultima_pagina])
    if x is not None and y is not None:
        return x, y, ultima_pagina

    # Buscar en la penúltima página si no se encontró en la última
    x, y = buscar_palabras_en_pagina(documento[penultima_pagina])
    if x is not None and y is not None:
        return x, y, penultima_pagina

    # Si no se encuentra en ninguna de las dos páginas
    return None, None, ultima_pagina
