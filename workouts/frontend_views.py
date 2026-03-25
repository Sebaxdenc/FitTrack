import json
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
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
from .models import Exercise, FavoriteExercise, MealItem, MealPlan, Routine, RoutineExercise, RoutineSchedule
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


class SocialFeedView(View):
    """
    Muestra el feed social con rutinas y planes de comidas públicos.
    No requiere autenticación pero lo recomendado es autenticarse para ver detalles.
    """
    template_name = "social_feed.html"

    def get(self, request):
        tab = request.GET.get("tab", "routines")
        selected_routine_id = request.GET.get("routine")
        selected_meal_plan_id = request.GET.get("meal")
        selected_exercise_id = request.GET.get("exercise")

        routines_qs = Routine.objects.filter(is_public=True).select_related("user").prefetch_related("exercises__exercise").order_by("-created_at")
        meal_plans_qs = MealPlan.objects.filter(is_public=True).select_related("user").prefetch_related("items__meal").order_by("-created_at")
        exercises_qs = Exercise.objects.exclude(user__isnull=True).select_related("user").order_by("-id")

        if request.user.is_authenticated:
            routines_qs = routines_qs.exclude(user=request.user)
            meal_plans_qs = meal_plans_qs.exclude(user=request.user)
            exercises_qs = exercises_qs.exclude(user=request.user)

        public_routines = routines_qs[:20]
        public_meal_plans = meal_plans_qs[:20]
        public_exercises = exercises_qs[:20]

        saved_routine_ids = set()
        saved_meal_plan_ids = set()
        saved_exercise_ids = set()
        if request.user.is_authenticated:
            saved_routine_ids = set(
                Routine.objects.filter(user=request.user, source_routine__isnull=False)
                .values_list("source_routine_id", flat=True)
            )
            saved_meal_plan_ids = set(
                MealPlan.objects.filter(user=request.user, source_meal_plan__isnull=False)
                .values_list("source_meal_plan_id", flat=True)
            )
            saved_exercise_ids = set(
                FavoriteExercise.objects.filter(user=request.user)
                .values_list("exercise_id", flat=True)
            )

        selected_routine = None
        routine_already_saved = False
        if selected_routine_id:
            selected_routine = routines_qs.filter(id=selected_routine_id).first()
            if selected_routine and request.user.is_authenticated:
                routine_already_saved = Routine.objects.filter(
                    user=request.user,
                    source_routine=selected_routine,
                ).exists()

        selected_meal_plan = None
        meal_plan_already_saved = False
        if selected_meal_plan_id:
            selected_meal_plan = meal_plans_qs.filter(id=selected_meal_plan_id).first()
            if selected_meal_plan and request.user.is_authenticated:
                meal_plan_already_saved = MealPlan.objects.filter(
                    user=request.user,
                    source_meal_plan=selected_meal_plan,
                ).exists()

        selected_exercise = None
        exercise_already_saved = False
        if selected_exercise_id:
            selected_exercise = exercises_qs.filter(id=selected_exercise_id).first()
            if selected_exercise and request.user.is_authenticated:
                exercise_already_saved = FavoriteExercise.objects.filter(
                    user=request.user,
                    exercise=selected_exercise,
                ).exists()

        return render(
            request,
            self.template_name,
            {
                "public_routines": public_routines,
                "public_meal_plans": public_meal_plans,
                "public_exercises": public_exercises,
                "is_authenticated": request.user.is_authenticated,
                "active_tab": tab if tab in {"routines", "meals", "exercises"} else "routines",
                "selected_routine": selected_routine,
                "selected_meal_plan": selected_meal_plan,
                "selected_exercise": selected_exercise,
                "routine_already_saved": routine_already_saved,
                "meal_plan_already_saved": meal_plan_already_saved,
                "exercise_already_saved": exercise_already_saved,
                "saved_routine_ids": saved_routine_ids,
                "saved_meal_plan_ids": saved_meal_plan_ids,
                "saved_exercise_ids": saved_exercise_ids,
            },
        )

    def post(self, request):
        routine_id = request.POST.get("routine_id")
        meal_plan_id = request.POST.get("meal_plan_id")
        exercise_id = request.POST.get("exercise_id")

        if meal_plan_id:
            if not request.user.is_authenticated:
                messages.error(request, "Debes iniciar sesion para guardar un plan de comida.")
                return redirect(f"/login/?next=/social/?tab=meals&meal={meal_plan_id}")

            source_plan = MealPlan.objects.filter(id=meal_plan_id, is_public=True).prefetch_related("items").first()
            if not source_plan:
                messages.error(request, "El plan de comida no existe o ya no esta disponible.")
                return redirect("/social/?tab=meals")

            if source_plan.user_id == request.user.id:
                messages.info(request, "Este plan de comida ya es tuyo.")
                return redirect(f"/social/?tab=meals&meal={source_plan.id}")

            if MealPlan.objects.filter(user=request.user, source_meal_plan=source_plan).exists():
                messages.info(request, "Ya guardaste este plan de comida.")
                return redirect(f"/social/?tab=meals&meal={source_plan.id}")

            with transaction.atomic():
                cloned_plan = MealPlan.objects.create(
                    user=request.user,
                    source_meal_plan=source_plan,
                    name=f"{source_plan.name} (Guardado)",
                    description=source_plan.description,
                    is_public=False,
                )

                meal_items = [
                    MealItem(
                        meal_plan=cloned_plan,
                        meal=item.meal,
                        quantity=item.quantity,
                        meal_type=item.meal_type,
                        sort_order=item.sort_order,
                    )
                    for item in source_plan.items.all()
                ]
                MealItem.objects.bulk_create(meal_items)

            messages.success(request, "Plan de comida guardado correctamente.")
            return redirect(f"/social/?tab=meals&meal={source_plan.id}")

        if exercise_id:
            if not request.user.is_authenticated:
                messages.error(request, "Debes iniciar sesion para guardar un ejercicio.")
                return redirect(f"/login/?next=/social/?tab=exercises&exercise={exercise_id}")

            source_exercise = Exercise.objects.filter(id=exercise_id).first()
            if not source_exercise:
                messages.error(request, "El ejercicio no existe o ya no esta disponible.")
                return redirect("/social/?tab=exercises")

            if source_exercise.user_id == request.user.id:
                messages.info(request, "Este ejercicio ya es tuyo.")
                return redirect(f"/social/?tab=exercises&exercise={source_exercise.id}")

            favorite, created = FavoriteExercise.objects.get_or_create(
                user=request.user,
                exercise=source_exercise,
            )
            if created:
                messages.success(request, "Ejercicio guardado en favoritos.")
            else:
                messages.info(request, "Este ejercicio ya esta guardado en favoritos.")
            return redirect(f"/social/?tab=exercises&exercise={source_exercise.id}")

        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesion para guardar una rutina.")
            return redirect(f"/login/?next=/social/?tab=routines&routine={routine_id}")

        source = Routine.objects.filter(id=routine_id, is_public=True).prefetch_related("exercises").first()
        if not source:
            messages.error(request, "La rutina no existe o ya no esta disponible.")
            return redirect("social-feed")

        if source.user_id == request.user.id:
            messages.info(request, "Esta rutina ya es tuya.")
            return redirect(f"/social/?tab=routines&routine={source.id}")

        if Routine.objects.filter(user=request.user, source_routine=source).exists():
            messages.info(request, "Ya guardaste esta rutina en tu lista.")
            return redirect(f"/social/?tab=routines&routine={source.id}")

        with transaction.atomic():
            cloned = Routine.objects.create(
                user=request.user,
                name=f"{source.name} (Guardada)",
                source_routine=source,
                goal=source.goal,
                description=source.description,
                is_public=False,
            )

            routine_exercises = [
                RoutineExercise(
                    routine=cloned,
                    exercise=item.exercise,
                    sort_order=item.sort_order,
                    target_sets=item.target_sets,
                    target_reps=item.target_reps,
                    rest_seconds=item.rest_seconds,
                )
                for item in source.exercises.all()
            ]
            RoutineExercise.objects.bulk_create(routine_exercises)

        messages.success(request, "Rutina guardada en tu lista de rutinas.")
        return redirect(f"/social/?tab=routines&routine={source.id}")
