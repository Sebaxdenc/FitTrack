from dataclasses import dataclass

from django.conf import settings

from .exceptions import (
    ExerciseDescriptionConfigurationError,
    ExerciseDescriptionGenerationError,
)

DEFAULT_EXERCISE_DESCRIPTION_MODEL = "gemini-2.5-flash"


@dataclass(frozen=True)
class ExerciseDescriptionInput:
    name: str
    muscle_group: str
    current_description: str = ""


def generate_exercise_description(*, name, muscle_group, current_description=""):
    payload = ExerciseDescriptionInput(
        name=name.strip(),
        muscle_group=muscle_group.strip(),
        current_description=(current_description or "").strip(),
    )
    return GeminiExerciseDescriptionService().generate_description(payload)


class GeminiExerciseDescriptionService:
    def __init__(self, *, api_key=None, model=DEFAULT_EXERCISE_DESCRIPTION_MODEL):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model

    def generate_description(self, payload):
        if not self.api_key:
            raise ExerciseDescriptionConfigurationError(
                "La generacion con IA no esta configurada en este entorno."
            )

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ExerciseDescriptionConfigurationError(
                "La dependencia de Gemini no esta instalada."
            ) from exc

        client = genai.Client(api_key=self.api_key)

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=_build_user_prompt(payload),
                config=types.GenerateContentConfig(
                    system_instruction=_build_system_instructions(),
                    temperature=0.4,
                ),
            )
        except Exception as exc:
            raise ExerciseDescriptionGenerationError(
                "No pudimos generar la descripcion en este momento."
            ) from exc

        description = (response.text or "").strip()
        if not description:
            raise ExerciseDescriptionGenerationError(
                "La IA no devolvio una descripcion valida."
            )
        return description


def _build_system_instructions():
    return (
        "Eres un asistente que redacta descripciones de ejercicios de gimnasio en espanol. "
        "Debes responder solo con texto plano listo para pegar en un formulario. "
        "Escribe 2 o 3 frases claras, practicas y faciles de entender. "
        "Explica para que sirve el ejercicio y que grupo muscular trabaja. "
        "Si ya existe un borrador, debes mejorarlo y reescribirlo manteniendo su intencion. "
        "No uses markdown, emojis, listas, advertencias medicas ni texto promocional."
    )


def _build_user_prompt(payload):
    current_description = payload.current_description or "Sin descripcion previa."
    return (
        f"Nombre del ejercicio: {payload.name}\n"
        f"Grupo muscular: {payload.muscle_group}\n"
        f"Descripcion actual: {current_description}\n\n"
        "Genera una nueva descripcion final para reemplazar el texto actual."
    )
