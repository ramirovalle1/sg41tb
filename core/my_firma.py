import json
import os
import subprocess
from settings import BASE_DIR
from datetime import datetime
from django.conf import settings
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12


class MY_JavaFirmaEc:
    def __init__(self, archivo_a_firmar, archivo_certificado, extension_certificado, password_certificado: str,
                 page="1", reason="", type_file="pdf", lx="10", ly="100", type_sign="QR"):
        self.archivo_a_firmar = archivo_a_firmar
        self.archivo_certificado = archivo_certificado
        self.extension_certificado = extension_certificado
        self.password_certificado = password_certificado.encode('utf-8')
        self.page = str(int(page) + 1)
        self.reason = reason
        self.type_file = type_file.lower()
        self.lx = str(int(lx))
        self.ly = str(int(ly))
        self.type_sign = type_sign
        self.jar_file = settings.JAR_FIRMA_EC
        self.java_path = settings.JAVA_20_EXECUTABLE
        self.datos_del_certificado = self.__obtener_datos_del_certificado()

    def __generar_nombre_archivo_temporal(self, extension: str) -> str:
        filename = datetime.now().strftime("%Y%m%d%H%M%S%f") + f".{extension}"
        print(f"__generar_nombre_archivo_temporal: {filename}")
        return os.path.join(settings.MEDIA_ROOT, 'archivos_temporales', filename)

    def __crear_archivo_temporal(self, data: bytes, extension: str) -> str:
        directorio = os.path.join(settings.MEDIA_ROOT, 'archivos_temporales')
        os.makedirs(directorio, exist_ok=True)
        path_archivo_temporal = self.__generar_nombre_archivo_temporal(extension)
        with open(path_archivo_temporal, "wb") as temp_file:
            temp_file.write(data)
        return path_archivo_temporal

    def __guardar_archivo_en_el_disco(self, archivo, extension: str) -> str:
        data = archivo.read() if not isinstance(archivo, bytes) else archivo
        return self.__crear_archivo_temporal(data, extension)

    def guardar_archivo_a_firmar_en_el_disco_and_get_path(self) -> str:
        return self.__guardar_archivo_en_el_disco(self.archivo_a_firmar, self.type_file)

    def guardar_archivo_certificado_en_el_disco_and_get_path(self) -> str:
        return self.__guardar_archivo_en_el_disco(self.archivo_certificado, self.extension_certificado)

    def __validar_certificado(self) -> bool:
        try:
            p12 = pkcs12.load_key_and_certificates(self.archivo_certificado, self.password_certificado,
                                                   default_backend())
            fecha_expiracion = max([p12[1].not_valid_after_utc] + [cert.not_valid_after_utc for cert in p12[2]])
            if datetime.now().date() >= fecha_expiracion.date():
                return False
            return self.datos_del_certificado.get("certificadoDigitalValido", False)
        except Exception as ex:
            raise ValueError(f"Error al validar el certificado: {ex}")

    def __obtener_datos_del_certificado(self) -> dict:
        path_certificate = self.guardar_archivo_certificado_en_el_disco_and_get_path()
        try:
            completed_process = subprocess.run(
                [
                    self.java_path, "-jar", self.jar_file, "-path_certificate", path_certificate,
                    "-password_certificate", self.password_certificado.decode('utf-8'), "-type_file",
                    "validar_certificado"
                ],
                timeout=10000, text=True, capture_output=True
            )
            if completed_process.returncode != 0 or not completed_process.stdout:
                raise ValueError("Error al obtener datos del certificado o API fuera de servicio.")
            return json.loads(completed_process.stdout)
        except subprocess.TimeoutExpired:
            raise ValueError("El proceso de validación del certificado ha superado el tiempo de espera.")
        except json.JSONDecodeError:
            raise ValueError("La respuesta de la API de firma EC no es un JSON válido.")
        except Exception as ex:
            raise ValueError(f"Error al obtener datos del certificado: {ex}")
        finally:
            os.remove(path_certificate)

    def sign_and_get_content_bytes(self) -> bytes:
        if not self.__validar_certificado():
            raise ValueError("Certificado no es válido")

        path_file_to_sign = self.guardar_archivo_a_firmar_en_el_disco_and_get_path()
        path_certificate = self.guardar_archivo_certificado_en_el_disco_and_get_path()

        try:
            completed_process = subprocess.run(
                [
                    self.java_path, "-jar", self.jar_file, "-path_file", path_file_to_sign, "-path_certificate",
                    path_certificate,
                    "-password_certificate", self.password_certificado.decode('utf-8'), "-page", self.page,
                    "-type_file",
                    self.type_file, "-lx", self.lx, "-ly", self.ly, "-type_sign", self.type_sign
                ] + (["-reason", self.reason] if self.reason else []),
                timeout=10000, text=True, capture_output=True
            )
            if completed_process.returncode != 0 or not completed_process.stdout:
                raise ValueError(f"Error en el proceso de firma: {completed_process.stderr}")

            data = json.loads(completed_process.stdout)
            path_signed_file = data.get("path_signed_file")
            if not path_signed_file or not os.path.exists(path_signed_file):
                raise ValueError("No se generó el archivo firmado correctamente.")

            with open(path_signed_file, "rb") as signed_file:
                return signed_file.read()
        except subprocess.TimeoutExpired:
            raise ValueError("El proceso de firma ha superado el tiempo de espera.")
        except json.JSONDecodeError:
            raise ValueError("La respuesta de la API de firma EC no es un JSON válido.")
        except Exception as ex:
            print(' ERROR EN EXCEPCION DE FIRMA '+str(ex))
            raise ValueError(f"Error al firmar el documento: {ex}")
        finally:
            os.remove(path_file_to_sign)
            os.remove(path_certificate)
            if path_signed_file:
                os.remove(path_signed_file)

