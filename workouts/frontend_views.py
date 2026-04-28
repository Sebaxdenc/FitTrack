import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View

from .ai_services import generate_exercise_description
from .exceptions import (
    ExerciseAccessDeniedError,
    ExerciseDescriptionConfigurationError,
    ExerciseDescriptionGenerationError,
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
    template_name = "dashboard/home.html"

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
                    description=form.cleaned_data["description"],
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


class ExerciseDescriptionGenerateView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"error": "La solicitud no tiene un formato valido."}, status=400)

        name = (payload.get("name") or "").strip()
        muscle_group = (payload.get("muscle_group") or "").strip()
        current_description = (payload.get("description") or "").strip()

        if not name or not muscle_group:
            return JsonResponse(
                {"error": "Debes completar nombre y grupo muscular antes de usar la IA."},
                status=400,
            )

        try:
            description = generate_exercise_description(
                name=name,
                muscle_group=muscle_group,
                current_description=current_description,
            )
        except ExerciseDescriptionConfigurationError as exc:
            return JsonResponse({"error": str(exc)}, status=503)
        except ExerciseDescriptionGenerationError as exc:
            return JsonResponse({"error": str(exc)}, status=502)

        return JsonResponse({"description": description})


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
