"""Pruebas unitarias locales: no requieren GUI, red ni clave de Gemini."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gemini_client


class PruebasAsistente(unittest.TestCase):
    def test_cargar_servicios(self):
        with tempfile.TemporaryDirectory() as temporal:
            archivo = Path(temporal) / "servicios.txt"
            archivo.write_text("Corte: 20 euros", encoding="utf-8")
            self.assertEqual(gemini_client.cargar_servicios(archivo), "Corte: 20 euros")

    def test_cargar_servicios_informa_si_falta(self):
        with self.assertRaisesRegex(FileNotFoundError, "No se encuentra"):
            gemini_client.cargar_servicios(Path("archivo_que_no_existe.txt"))

    def test_procesar_json_correcto(self):
        resultado = gemini_client.procesar_respuesta_json(
            json.dumps({"respuesta": "El corte cuesta 24 €."}, ensure_ascii=False)
        )
        self.assertEqual(resultado, "El corte cuesta 24 €.")

    def test_procesar_json_malformado(self):
        with self.assertRaisesRegex(ValueError, "no se pudo leer"):
            gemini_client.procesar_respuesta_json("esto no es JSON")

    def test_procesar_json_sin_campo_requerido(self):
        with self.assertRaisesRegex(ValueError, "no contiene el campo"):
            gemini_client.procesar_respuesta_json('{"texto": "hola"}')

    def test_timeout_se_considera_error_transitorio(self):
        self.assertTrue(gemini_client._es_error_transitorio(TimeoutError("request timed out")))

        class Error504(Exception):
            code = 504

        self.assertTrue(gemini_client._es_error_transitorio(Error504("DEADLINE_EXCEEDED")))

    @patch.dict("os.environ", {"GEMINI_API_KEY": ""}, clear=False)
    def test_no_consulta_sin_clave(self):
        with patch.dict("os.environ", {"API_KEY": ""}, clear=False):
            with patch.object(gemini_client, "load_dotenv"), self.assertRaisesRegex(RuntimeError, "Falta la clave"):
                gemini_client.responder_consulta("¿Qué servicios hay?")

    def test_consulta_usa_gemini_y_procesa_json(self):
        class RespuestaFalsa:
            text = '{"respuesta": "Tenemos corte y coloración."}'

        class ModelosFalsos:
            def __init__(self):
                self.argumentos = None

            def generate_content(self, **kwargs):
                self.argumentos = kwargs
                return RespuestaFalsa()

        modelos = ModelosFalsos()

        class ClienteFalso:
            def __init__(self, api_key, http_options=None):
                self.api_key = api_key
                self.http_options = http_options
                self.models = modelos

        with patch.dict("os.environ", {"GEMINI_API_KEY": "clave-de-prueba", "GEMINI_MODEL": "modelo-de-prueba"}, clear=False):
            with patch.object(gemini_client, "load_dotenv"), \
                 patch.object(gemini_client.genai, "Client", ClienteFalso):
                texto = gemini_client.responder_consulta("¿Qué servicios hay?")

        self.assertEqual(texto, "Tenemos corte y coloración.")
        self.assertEqual(modelos.argumentos["model"], "modelo-de-prueba")
        self.assertIn("servicios", modelos.argumentos["contents"])
        self.assertEqual(modelos.argumentos["config"].response_mime_type, "application/json")
        self.assertEqual(modelos.argumentos["config"].thinking_config.thinking_level.value.lower(), "minimal")
        self.assertEqual(modelos.argumentos["config"].max_output_tokens, 192)

    def test_usa_modelo_respaldo_si_el_principal_devuelve_503(self):
        class Error503(Exception):
            code = 503

        class RespuestaFalsa:
            text = '{"respuesta": "El sábado abrimos por la mañana."}'

        class ModelosFalsos:
            def __init__(self):
                self.modelos_consultados = []

            def generate_content(self, **kwargs):
                self.modelos_consultados.append(kwargs["model"])
                if kwargs["model"] == "modelo-principal-prueba":
                    raise Error503("UNAVAILABLE: high demand")
                return RespuestaFalsa()

        modelos = ModelosFalsos()

        class ClienteFalso:
            def __init__(self, api_key, http_options=None):
                self.http_options = http_options
                self.models = modelos

        variables = {
            "GEMINI_API_KEY": "clave-de-prueba",
            "GEMINI_MODEL": "modelo-principal-prueba",
            "GEMINI_FALLBACK_MODEL": "modelo-respaldo-prueba",
        }
        with patch.dict("os.environ", variables, clear=False):
            with patch.object(gemini_client, "load_dotenv"):
                with patch.object(gemini_client.genai, "Client", ClienteFalso):
                    respuesta = gemini_client.responder_consulta("¿Cuál es el horario?")

        self.assertEqual(respuesta, "El sábado abrimos por la mañana.")
        self.assertEqual(modelos.modelos_consultados, ["modelo-principal-prueba", "modelo-respaldo-prueba"])


if __name__ == "__main__":
    unittest.main()



