from django.db import transaction
import logging
import os
import json
import requests


from .exceptions import (
    ExerciseAccessDeniedError,
    ExerciseNotFoundError,
    RoutineAccessDeniedError,
    RoutineNotFoundError,
    RoutineValidationError,
)
from .models import Exercise, Routine, RoutineExercise, RoutineSchedule

logger = logging.getLogger(__name__)

def create_exercise(*, user, name, muscle_group, description, image_url="", equipment_photo=None):
    return Exercise.objects.create(
        user=user,
        name=name.strip(),
        muscle_group=muscle_group.strip(),
        description=description.strip(),
        image_url=image_url.strip(),
        equipment_photo=equipment_photo,
    )


def delete_exercise(*, user, exercise_id):
    exercise = Exercise.objects.filter(id=exercise_id).first()
    if not exercise:
        raise ExerciseNotFoundError("El ejercicio no existe.")
    if exercise.user_id != user.id:
        raise ExerciseAccessDeniedError("No puedes eliminar este ejercicio.")
    if exercise.equipment_photo:
        exercise.equipment_photo.delete(save=False)
    exercise.delete()


def _build_routine_exercise_payload(*, user, exercise_items):
    if not exercise_items:
        raise RoutineValidationError("La rutina debe tener al menos un ejercicio.")

    payload = []
    seen_orders = set()

    for index, item in enumerate(exercise_items, start=1):
        exercise = Exercise.objects.filter(id=item["exercise_id"], user=user).first()
        if not exercise:
            raise ExerciseNotFoundError("Uno de los ejercicios seleccionados no existe.")

        sort_order = int(item.get("sort_order") or index)
        if sort_order in seen_orders:
            raise RoutineValidationError("El orden de los ejercicios debe ser unico.")
        seen_orders.add(sort_order)

        target_sets = int(item.get("target_sets") or 1)
        target_reps = int(item.get("target_reps") or 1)
        rest_seconds = int(item.get("rest_seconds") or 0)

        if target_sets < 1 or target_reps < 1 or rest_seconds < 0:
            raise RoutineValidationError("Sets, repeticiones y descanso deben ser valores validos.")

        payload.append(
            {
                "exercise": exercise,
                "sort_order": sort_order,
                "target_sets": target_sets,
                "target_reps": target_reps,
                "rest_seconds": rest_seconds,
            }
        )

    return payload


@transaction.atomic
def create_routine(*, user, name, goal, is_public, exercise_items, scheduled_days):
    if not name.strip():
        raise RoutineValidationError("La rutina debe tener nombre.")

    routine_exercise_payload = _build_routine_exercise_payload(
        user=user,
        exercise_items=exercise_items,
    )

    routine = Routine.objects.create(
        user=user,
        name=name.strip(),
        goal=goal.strip(),
        is_public=is_public,
    )

    RoutineExercise.objects.bulk_create(
        [
            RoutineExercise(routine=routine, **item)
            for item in routine_exercise_payload
        ]
    )

    assign_routine_to_days(
        user=user,
        routine=routine,
        scheduled_days=scheduled_days,
    )
    return routine


@transaction.atomic
def assign_routine_to_days(*, user, routine, scheduled_days):
    if routine.user_id != user.id:
        raise RoutineAccessDeniedError("No puedes asignar una rutina que no te pertenece.")

    normalized_days = sorted({int(day) for day in scheduled_days})
    for day in normalized_days:
        if day not in range(7):
            raise RoutineValidationError("Los dias de la semana no son validos.")
        RoutineSchedule.objects.update_or_create(
            user=user,
            day_of_week=day,
            defaults={"routine": routine},
        )

    return routine


@transaction.atomic
def delete_routine(*, user, routine_id):
    routine = Routine.objects.filter(id=routine_id).first()
    if not routine:
        raise RoutineNotFoundError("La rutina no existe.")
    if routine.user_id != user.id:
        raise RoutineAccessDeniedError("No puedes eliminar esta rutina.")
    routine.delete()


def get_ai_recommendations(stats_data):
    prompt = f"""
    Eres un entrenador personal.

    Basado en estos datos:
    {json.dumps(stats_data, indent=2)}

    Analiza mis estadisticas
    """

    hf_token = os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN")
    if not hf_token:
        raise ValueError("No hay token de Hugging Face configurado. Usa HUGGINGFACE_API_TOKEN o HF_TOKEN en tu .env")

    model = os.getenv("HUGGINGFACE_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    api_url = os.getenv("HUGGINGFACE_API_URL", "https://router.huggingface.co/v1/chat/completions")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Eres un entrenador personal experto. Responde siempre en espanol y en texto normal (no md)",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 500,
    }

    try:
        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {hf_token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )

        if response.status_code >= 400:
            raise ValueError(f"Hugging Face devolvio {response.status_code}: {response.text[:300]}")

        data = response.json()
        text = ""
        choices = data.get("choices") if isinstance(data, dict) else None
        if choices and isinstance(choices, list):
            text = (choices[0].get("message", {}) or {}).get("content", "").strip()

        if not text:
            raise ValueError("Hugging Face no devolvio recomendaciones en texto.")

        return text
    except Exception as exc:
        logger.exception("Error obteniendo recomendaciones de IA")
        raise ValueError(f"No se pudieron generar recomendaciones: {exc}") from exc
