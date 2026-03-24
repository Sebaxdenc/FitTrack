import json
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from .exceptions import (
    ExerciseAccessDeniedError,
    ExerciseError,
    RoutineAccessDeniedError,
    RoutineError,
    RoutineNotFoundError,
)
from .forms import LoginForm, RegistrationForm
from .models import RoutineSchedule
from .routine_forms import ExerciseCreateForm, RoutineCreateForm
from .selectors import (
    get_todays_routine_schedule,
    get_user_exercises,
    get_user_routine,
    get_user_routines,
    get_user_weekly_schedule,
    get_user_stats
)
from .services import create_exercise, create_routine, delete_exercise, delete_routine


class LoginView(View):
    template_name = "auth/login.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "form": LoginForm(),
                "next_url": request.GET.get("next", ""),
            },
        )

    def post(self, request):
        form = LoginForm(request.POST)
        next_url = request.POST.get("next") or "dashboard-home"
        if form.is_valid():
            login(request, form.cleaned_data["user"])
            messages.success(request, "Inicio de sesion exitoso.")
            return redirect(next_url)
        messages.error(request, "No pudimos iniciar sesion. Revisa tus datos.")
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "next_url": next_url,
            },
        )


class RegisterView(View):
    template_name = "auth/register.html"

    def get(self, request):
        return render(request, self.template_name, {"form": RegistrationForm()})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cuenta creada correctamente. Inicia sesion para continuar.")
            return redirect("auth-login")
        messages.error(request, "Revisa los campos del registro para continuar.")
        return render(request, self.template_name, {"form": form})


class HomeView(LoginRequiredMixin, View):
    template_name = "dashboard/base.html"

    def get(self, request):
        sample_meal = {
            "title": "Pescado y Verduras",
            "subtitle": "Ejemplo dinner dependiendo de la hora",
            "time_range": "7pm - 9pm",
        }
        routine_schedule = get_todays_routine_schedule(request.user)
        routine = routine_schedule.routine if routine_schedule else None
        routine_exercises = []
        if routine:
            routine_exercises = list(routine.exercises.select_related("exercise").all()[:6])

        return render(
            request,
            self.template_name,
            {
                "user": request.user,
                "meal": sample_meal,
                "routine_schedule": routine_schedule,
                "routine": routine,
                "routine_exercises": routine_exercises,
                "day_labels": dict(RoutineSchedule.DAY_CHOICES),
            },
        )


class LandingView(View):
    template_name = "landing.html"

    def get(self, request):
        return render(request, self.template_name)


class ExerciseListView(LoginRequiredMixin, View):
    template_name = "exercises_index.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "exercise_form": ExerciseCreateForm(),
                "exercises": get_user_exercises(request.user),
            },
        )

    def post(self, request):
        form = ExerciseCreateForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                create_exercise(
                    user=request.user,
                    name=form.cleaned_data["name"],
                    muscle_group=form.cleaned_data["muscle_group"],
                    exercise_type=form.cleaned_data["type"],
                    image_url=form.cleaned_data["image_url"],
                    equipment_photo=form.cleaned_data["equipment_photo"],
                )
                messages.success(request, "Ejercicio creado correctamente.")
                return redirect("routine-exercise-list")
            except ExerciseError as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, "Revisa los datos del ejercicio para continuar.")

        return render(
            request,
            self.template_name,
            {
                "exercise_form": form,
                "exercises": get_user_exercises(request.user),
            },
        )


class ExerciseDeleteView(LoginRequiredMixin, View):
    def post(self, request, exercise_id):
        try:
            delete_exercise(user=request.user, exercise_id=exercise_id)
            messages.success(request, "Ejercicio eliminado.")
        except (ExerciseError, ExerciseAccessDeniedError) as exc:
            messages.error(request, str(exc))
        return redirect("routine-exercise-list")


class RoutineListView(LoginRequiredMixin, View):
    template_name = "routines_index.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "routines": get_user_routines(request.user),
                "weekly_schedule": get_user_weekly_schedule(request.user),
                "exercises": get_user_exercises(request.user)[:6],
                "day_labels": dict(RoutineSchedule.DAY_CHOICES),
            },
        )


class RoutineCreateView(LoginRequiredMixin, View):
    template_name = "routines_create.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "form": RoutineCreateForm(),
                "exercise_choices": list(get_user_exercises(request.user)),
            },
        )

    def post(self, request):
        form = RoutineCreateForm(request.POST)
        exercise_choices = list(get_user_exercises(request.user))

        if form.is_valid():
            try:
                create_routine(
                    user=request.user,
                    name=form.cleaned_data["name"],
                    goal=form.cleaned_data["goal"],
                    is_public=form.cleaned_data["is_public"],
                    exercise_items=_extract_routine_exercises(request),
                    scheduled_days=form.cleaned_data["scheduled_days"],
                )
                messages.success(request, "Rutina creada correctamente.")
                return redirect("routine-list")
            except RoutineError as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, "Revisa los datos de la rutina para continuar.")

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "exercise_choices": exercise_choices,
            },
        )


class RoutineDetailView(LoginRequiredMixin, View):
    template_name = "routines_detail.html"

    def get(self, request, routine_id):
        routine = get_user_routine(request.user, routine_id)
        if not routine:
            messages.error(request, "La rutina que buscas no existe.")
            return redirect("routine-list")

        return render(
            request,
            self.template_name,
            {
                "routine": routine,
                "weekly_schedule": get_user_weekly_schedule(request.user).filter(routine=routine),
                "day_labels": dict(RoutineSchedule.DAY_CHOICES),
            },
        )


class RoutineDeleteView(LoginRequiredMixin, View):
    def post(self, request, routine_id):
        try:
            delete_routine(user=request.user, routine_id=routine_id)
            messages.success(request, "Rutina eliminada.")
        except (RoutineError, RoutineAccessDeniedError, RoutineNotFoundError) as exc:
            messages.error(request, str(exc))
        return redirect("routine-list")

#TODO: Pass data from the selector to the template for present in dashboards
class StatsView(LoginRequiredMixin, View):
    template_name = "dashboard/stats.html"
 
    def get(self, request):
        stats = get_user_stats(request.user)
 
        # Serialize chart data to JSON for use in JavaScript
        weekly_workout_json = json.dumps(stats["weekly_workout_data"])
        weekly_calorie_json = json.dumps(stats["weekly_calorie_data"])
        goals_by_week_json = json.dumps(stats["goals_by_week"])
 
        return render(
            request,
            self.template_name,
            {
                "user": request.user,
                "stats": stats,
                # Pre-serialized for Chart.js
                "weekly_workout_json": weekly_workout_json,
                "weekly_calorie_json": weekly_calorie_json,
                "goals_by_week_json": goals_by_week_json,
                "day_labels": dict(RoutineSchedule.DAY_CHOICES),
            },
        )
            



def _extract_routine_exercises(request):
    exercise_items = []

    for key in request.POST:
        if not key.startswith("selected_exercise_"):
            continue

        exercise_id = key.rsplit("_", 1)[-1]
        if request.POST.get(key) != "on":
            continue

        exercise_items.append(
            {
                "exercise_id": exercise_id,
                "sort_order": request.POST.get(f"sort_order_{exercise_id}") or len(exercise_items) + 1,
                "target_sets": request.POST.get(f"target_sets_{exercise_id}") or 3,
                "target_reps": request.POST.get(f"target_reps_{exercise_id}") or 10,
                "rest_seconds": request.POST.get(f"rest_seconds_{exercise_id}") or 60,
            }
        )

    return exercise_items
