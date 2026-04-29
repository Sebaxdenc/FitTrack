from django.db import transaction

from .exceptions import (
    ExerciseAccessDeniedError,
    ExerciseNotFoundError,
    RoutineAccessDeniedError,
    RoutineNotFoundError,
    RoutineValidationError,
)
from .models import Exercise, Routine, RoutineExercise, RoutineSchedule


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
    """
    Obtiene recomendaciones de IA basadas en las estadísticas del usuario.
    Utiliza OpenAI API para generar recomendaciones personalizadas.
    """
    import os
    from openai import OpenAI
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY no está configurada en las variables de entorno")
    
    client = OpenAI(api_key=api_key)
    
    # Construir el prompt con los datos de estadísticas
    prompt = f"""Basándote en las siguientes estadísticas de entrenamiento y salud del usuario, proporciona 3-5 recomendaciones específicas, prácticas y accionables en español:

ESTADÍSTICAS DEL USUARIO (últimos 7 días):
- Entrenamientos realizados: {stats_data.get('workouts_last_7', 0)}
- Duración promedio de sesión: {stats_data.get('avg_duration_minutes', 0):.0f} minutos
- Horas totales entrenadas: {stats_data.get('total_duration_hours', 0):.1f} horas
- Calorías quemadas (promedio diario): {stats_data.get('avg_calories_burned_7d', 0):.0f} kcal
- Calorías consumidas (promedio diario): {stats_data.get('avg_calories_consumed_7d', 0):.0f} kcal
- Racha actual: {stats_data.get('current_streak', 0)} días
- Tasa de cumplimiento de metas: {stats_data.get('goal_completion_rate', 0):.1f}%
- Total de entrenamientos realizados: {stats_data.get('total_workouts', 0)}
- Total de rutinas creadas: {stats_data.get('total_routines', 0)}

Por favor, proporciona recomendaciones que:
1. Sean específicas basadas en estos números
2. Incluyan consejos de entrenamiento, nutrición o recuperación
3. Sean motivacionales pero realistas
4. Ayuden al usuario a mejorar su progreso

Formatea la respuesta como una lista con viñetas claras y concisas."""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Eres un coach personal y nutricionista experto que proporciona recomendaciones prácticas basadas en datos de salud y entrenamiento. Siempre respondes en español."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    return response.choices[0].message.content
