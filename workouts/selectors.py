from datetime import date

from django.db.models import Prefetch

from .models import Exercise, Routine, RoutineExercise, RoutineSchedule


def get_user_exercises(user):
    return Exercise.objects.filter(user=user).order_by("name")


def get_user_routines(user):
    routine_exercises = RoutineExercise.objects.select_related("exercise").order_by("sort_order")
    return (
        Routine.objects.filter(user=user)
        .prefetch_related(Prefetch("exercises", queryset=routine_exercises))
        .order_by("-created_at", "name")
    )


def get_user_routine(user, routine_id):
    return get_user_routines(user).filter(id=routine_id).first()


def get_user_weekly_schedule(user):
    return (
        RoutineSchedule.objects.filter(user=user)
        .select_related("routine")
        .order_by("day_of_week")
    )


def get_todays_routine_schedule(user, target_date=None):
    current_date = target_date or date.today()
    return (
        RoutineSchedule.objects.filter(user=user, day_of_week=current_date.weekday())
        .select_related("routine")
        .first()
    )
