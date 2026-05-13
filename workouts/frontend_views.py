import json
import time

from django.http import JsonResponse
import os
import base64
import requests as http_requests
from dotenv import load_dotenv
import logging
from functools import lru_cache
import numpy as np
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.views import View
from django.utils import timezone
from .models import Meal, FavoriteMeal, DailyLog, MealLog
from .forms import MealForm
from openai import OpenAI

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
from .models import Exercise, FavoriteExercise, MealItem, MealPlan, Routine, RoutineExercise, RoutineSchedule
from .models import Workout
from .routine_forms import ExerciseCreateForm, RoutineCreateForm
from .selectors import (
    get_todays_routine_schedule,
    get_user_exercises,
    get_user_routine,
    get_user_routines,
    get_user_weekly_schedule,
    get_user_stats
)
from django.contrib.messages import get_messages
from .services import create_exercise, create_routine, delete_exercise, delete_routine, _build_routine_exercise_payload


class WorkoutRunView(LoginRequiredMixin, View):
    template_name = "workout/run.html"

    def get(self, request, routine_id):
        routine = Routine.objects.filter(id=routine_id, user=request.user).prefetch_related('exercises__exercise').first()
        if not routine:
            messages.error(request, "Rutina no encontrada.")
            return redirect('routine-list')

        exercises = list(routine.exercises.order_by('sort_order'))
        total = len(exercises)
        if total == 0:
            messages.error(request, "La rutina no tiene ejercicios.")
            return redirect('routine-detail', routine_id=routine_id)

        # session key to track progress
        sess_key = f'workout_progress_{routine_id}'
        prog = request.session.get(sess_key, {})
        if not prog:
            prog = {'ex_index': 0, 'completed_sets': 0, 'started_at': timezone.now().isoformat()}
            request.session[sess_key] = prog

        ex_index = prog.get('ex_index', 0)
        completed_sets = prog.get('completed_sets', 0)

        # clamp
        if ex_index >= total:
            ex_index = total - 1

        current_ex = exercises[ex_index]

        context = {
            'routine': routine,
            'current_exercise': current_ex,
            'current_index_plus_one': ex_index + 1,
            'total_exercises': total,
            'range_current_sets': range(1, current_ex.target_sets + 1),
            'completed_sets': completed_sets,
        }
        return render(request, self.template_name, context)


class WorkoutCompleteSetView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, routine_id):
        routine = Routine.objects.filter(id=routine_id, user=request.user).prefetch_related('exercises__exercise').first()
        if not routine:
            return JsonResponse({'error': 'Rutina no encontrada.'}, status=404)

        exercises = list(routine.exercises.order_by('sort_order'))
        if not exercises:
            return JsonResponse({'error': 'Sin ejercicios'}, status=400)

        sess_key = f'workout_progress_{routine_id}'
        prog = request.session.get(sess_key, {})
        if not prog:
            prog = {'ex_index': 0, 'completed_sets': 0, 'started_at': timezone.now().isoformat()}

        ex_index = prog.get('ex_index', 0)
        completed_sets = prog.get('completed_sets', 0)

        # current exercise
        if ex_index >= len(exercises):
            # already finished
            request.session.pop(sess_key, None)
            messages.success(request, 'Rutina completada.')
            request.session["workout_completed_notice"] = {
                "routine_name": routine.name,
                "exercise_count": len(exercises),
            }
            return JsonResponse({'finished': True})

        current_ex = exercises[ex_index]

        # increment completed_sets
        completed_sets += 1

        # update stats: simplistic calories per set
        per_set_cal = 8
        today = timezone.localdate()
        daily_log, _ = DailyLog.objects.get_or_create(user=request.user, log_date=today)
        daily_log.total_calories_burned = (daily_log.total_calories_burned or 0) + per_set_cal
        daily_log.save()

        # if reached target sets, advance exercise
        if completed_sets >= current_ex.target_sets:
            ex_index += 1
            completed_sets = 0

        # if finished all exercises, finalize workout record
        if ex_index >= len(exercises):
            # create a Workout record
            started = prog.get('started_at')
            try:
                started_dt = timezone.datetime.fromisoformat(started)
                if started_dt.tzinfo is None:
                    started_dt = timezone.make_aware(started_dt)
            except Exception:
                started_dt = timezone.now()

            duration_minutes = 0
            Workout.objects.create(user=request.user, routine=routine, started_at=started_dt, duration_minutes=duration_minutes)
            request.session.pop(sess_key, None)
            messages.success(request, 'Rutina completada. Buen trabajo!')
            request.session["workout_completed_notice"] = {
                "routine_name": routine.name,
                "exercise_count": len(exercises),
            }
            return JsonResponse({'finished': True})

        prog['ex_index'] = ex_index
        prog['completed_sets'] = completed_sets
        request.session[sess_key] = prog
        request.session.modified = True

        return JsonResponse({'ok': True})


class WorkoutDaysView(LoginRequiredMixin, View):
    """Display all 7 days of the week with their scheduled routines."""
    template_name = "workout/days.html"

    def get(self, request):
        # Get all routine schedules for the user
        schedules = RoutineSchedule.objects.filter(user=request.user).select_related('routine')
        
        # Build a dict: day_of_week -> list of routines
        days_data = {}
        day_names = {
            0: "Lunes",
            1: "Martes",
            2: "Miércoles",
            3: "Jueves",
            4: "Viernes",
            5: "Sábado",
            6: "Domingo",
        }
        
        # Initialize all 7 days
        for day_num in range(7):
            days_data[day_num] = {
                'name': day_names[day_num],
                'routines': []
            }
        
        # Populate routines for each day
        for schedule in schedules:
            day_num = schedule.day_of_week
            days_data[day_num]['routines'].append(schedule.routine)
        
        # Sort by day number
        sorted_days = [days_data[i] for i in range(7)]
        
        context = {
            'days': sorted_days,
            'day_names': day_names,
        }
        return render(request, self.template_name, context)


#  Generación de imagen con Hugging Face

def _generate_meal_image_huggingface(meal_name: str):
    load_dotenv(".env")
    load_dotenv("../.env")

    hf_token = os.environ.get("HUGGINGFACE_API_TOKEN") or os.environ.get("HF_TOKEN")
    if not hf_token:
        return None

    prompt = (
        f"High quality food photography of '{meal_name}', "
        "served on a clean white plate, professional studio lighting, "
        "top-down view, appetizing, vibrant colors, no text."
    )

    model_name = os.environ.get(
        "HUGGINGFACE_IMAGE_MODEL",
        "black-forest-labs/FLUX.1-schnell",
    )
    url = f"https://router.huggingface.co/hf-inference/models/{model_name}"
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Accept": "image/png",
        "Content-Type": "application/json",
    }
    payload = {"inputs": prompt}

    safe_name = meal_name.replace(" ", "_").replace("/", "-")
    filename = f"m_{safe_name}.png"
    storage_path = os.path.join("meals", filename)

    last_error = None
    for attempt in range(3):
        try:
            response = http_requests.post(url, headers=headers, json=payload, timeout=120)

            if response.status_code == 503:
                time.sleep(2 ** attempt)
                continue

            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "image" not in content_type.lower():
                error_data = response.json() if response.content else {}
                raise ValueError(
                    f"Hugging Face no devolvio una imagen valida: {error_data}"
                )

            saved_path = default_storage.save(storage_path, ContentFile(response.content))

            return saved_path

        except Exception as exc:
            last_error = exc
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code != 429 or attempt == 2:
                logger.warning("No se pudo generar imagen para '%s' con Hugging Face: %s", meal_name, exc)
                return None
            time.sleep(2 ** attempt)

    logger.warning("No se pudo generar imagen para '%s' con Hugging Face: %s", meal_name, last_error)
    return None

logger = logging.getLogger(__name__)


def _cosine_similarity(a, b):
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    if denominator == 0:
        return 0.0
    return float(np.dot(a, b) / denominator)


def _expand_semantic_query(query):
    query = (query or "").strip().lower()
    if not query:
        return ""

    synonyms = {
        "street": ["street workout", "calistenia", "calisthenics", "entrenamiento callejero"],
        "calle": ["street workout", "calistenia", "calisthenics"],
        "calistenia": ["street workout", "bodyweight", "calisthenics"],
        "pierna": ["leg", "legs", "lower body"],
        "pecho": ["chest", "pectoral"],
        "espalda": ["back", "dorsal"],
        "proteina": ["protein", "high protein"],
        "definicion": ["cut", "lean", "shredded"],
    }

    expanded_terms = [query]
    for token in query.split():
        expanded_terms.extend(synonyms.get(token, []))

    unique_terms = []
    seen = set()
    for term in expanded_terms:
        if term and term not in seen:
            unique_terms.append(term)
            seen.add(term)

    return " ".join(unique_terms)


@lru_cache(maxsize=1)
def _get_huggingface_api_token():
    return os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("huggingface_apikey")


@lru_cache(maxsize=1)
def _has_embedding_provider_configured():
    return _get_openai_client() is not None or bool(_get_huggingface_api_token())


@lru_cache(maxsize=1)
def _get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("openai_apikey")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


@lru_cache(maxsize=2048)
def _get_openai_title_embedding_cached(title):
    client = _get_openai_client()
    response = client.embeddings.create(
        input=[title],
        model="text-embedding-3-small",
    )
    return np.array(response.data[0].embedding, dtype=np.float32)


def _rank_with_hf_sentence_similarity(items, query, title_attr):
    token = _get_huggingface_api_token()
    if not token:
        return None

    titles = []
    filtered_items = []
    for item in items:
        title = (getattr(item, title_attr, "") or "").strip()
        if not title:
            continue
        titles.append(title)
        filtered_items.append(item)

    if not titles:
        return []

    model_url = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2"
    response = http_requests.post(
        model_url,
        headers={"Authorization": f"Bearer {token}"},
        json={
            "inputs": {
                "source_sentence": query,
                "sentences": titles,
            },
            "options": {"wait_for_model": True},
        },
        timeout=45,
    )
    response.raise_for_status()
    scores = response.json()

    if not isinstance(scores, list):
        raise ValueError("Unexpected Hugging Face sentence-similarity response format")

    scored_items = []
    for item, score in zip(filtered_items, scores):
        score = float(score)
        item.semantic_score = score
        item.semantic_percent = max(0.0, min(1.0, score)) * 100
        scored_items.append((score, item))

    scored_items.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored_items]


def _get_title_embedding(title):
    client = _get_openai_client()
    if client:
        try:
            return _get_openai_title_embedding_cached(title), "openai"
        except Exception as exc:
            logger.warning("OpenAI embeddings failed: %s", exc)

    return None, "none"


def _semantic_rank_by_title(items, query, title_attr):
    query = (query or "").strip()
    if not query:
        return list(items), "none"

    expanded_query = _expand_semantic_query(query)
    query_embedding, provider = _get_title_embedding(expanded_query)
    if query_embedding is None:
        if _get_huggingface_api_token():
            try:
                ranked_items = _rank_with_hf_sentence_similarity(items, expanded_query, title_attr)
                if ranked_items is not None:
                    return ranked_items, "embedding", "huggingface"
            except Exception as exc:
                logger.warning("Hugging Face semantic ranking failed: %s", exc)

        lowered_query_tokens = set(expanded_query.lower().split())
        if not lowered_query_tokens:
            lowered_query_tokens = {query.lower()}
        return (
            [
                item for item in items
                if any(
                    token in (getattr(item, title_attr, "") or "").lower()
                    for token in lowered_query_tokens
                )
            ],
            "text",
            "none",
        )

    scored_items = []
    for item in items:
        title = getattr(item, title_attr, "") or ""
        if not title:
            continue

        title_embedding, _ = _get_title_embedding(title)
        if title_embedding is None:
            continue

        score = _cosine_similarity(query_embedding, title_embedding)
        item.semantic_score = score
        item.semantic_percent = max(0.0, min(1.0, score)) * 100
        scored_items.append((score, item))

    scored_items.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored_items], "embedding", provider


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
        today_weekday = timezone.localdate().weekday()
        weekly_schedule = {
            schedule.day_of_week: schedule
            for schedule in get_user_weekly_schedule(request.user).select_related("routine")
        }

        # Default exercises not shown in the UI; omit from context

        calendar_days = []
        for day_index, day_label in RoutineSchedule.DAY_CHOICES:
            schedule = weekly_schedule.get(day_index)
            routine = schedule.routine if schedule else None
            routine_exercises = []
            if routine:
                routine_exercises = list(
                    routine.exercises.select_related("exercise").order_by("sort_order")[:4]
                )

            # compute the date for this weekday in the current week
            today = timezone.localdate()
            days_ahead = (day_index - today_weekday) % 7
            target_date = today + timezone.timedelta(days=days_ahead)

            # fetch meal logs for this date (if any)
            daily_log = DailyLog.objects.filter(user=request.user, log_date=target_date).first()
            meal_logs = []
            if daily_log:
                meal_logs = list(daily_log.meals.select_related('meal').order_by('eaten_at'))

            calendar_days.append(
                {
                    "index": day_index,
                    "label": day_label,
                    "is_today": day_index == today_weekday,
                    "schedule": schedule,
                    "routine": routine,
                    "routine_exercises": routine_exercises,
                    "exercise_count": len(routine_exercises),
                    "target_date": target_date,
                    "meal_logs": meal_logs,
                }
            )

        # Deduplicate flashed messages so identical messages don't stack
        storage = get_messages(request)
        seen = set()
        deduped = []
        for m in storage:
            text = str(m)
            if text in seen:
                continue
            seen.add(text)
            deduped.append(m)

        return render(
            request,
            self.template_name,
            {
                "user": request.user,
                "calendar_days": calendar_days,
                "day_labels": dict(RoutineSchedule.DAY_CHOICES),
                "dashboard_messages": deduped,
                "workout_completed_notice": request.session.pop("workout_completed_notice", None),
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
                # If caller provided a return URL, go back there (e.g., routine create flow)
                next_url = request.POST.get("next") or request.GET.get("next")
                if next_url:
                    return redirect(next_url)
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
                    scheduled_days=[],
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


class RoutineEditView(LoginRequiredMixin, View):
    template_name = "routines_edit.html"

    def get(self, request, routine_id):
        routine = get_user_routine(request.user, routine_id)
        if not routine:
            messages.error(request, "La rutina que buscas no existe.")
            return redirect("routine-list")

        form = RoutineCreateForm(initial={
            "name": routine.name,
            "goal": routine.goal,
            "is_public": "True" if routine.is_public else "False",
        })
        
        exercise_choices = list(get_user_exercises(request.user))
        
        # Mark exercises that are in this routine
        routine_exercise_ids = set(routine.exercises.values_list("exercise_id", flat=True))
        for exercise in exercise_choices:
            exercise.in_routine = exercise.id in routine_exercise_ids

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "exercise_choices": exercise_choices,
                "routine": routine,
                "routine_id": routine_id,
            },
        )

    def post(self, request, routine_id):
        routine = get_user_routine(request.user, routine_id)
        if not routine:
            messages.error(request, "La rutina que buscas no existe.")
            return redirect("routine-list")

        form = RoutineCreateForm(request.POST)
        exercise_choices = list(get_user_exercises(request.user))

        if form.is_valid():
            try:
                # Update routine basic info
                routine.name = form.cleaned_data["name"]
                routine.goal = form.cleaned_data["goal"]
                routine.is_public = form.cleaned_data["is_public"]
                routine.save()

                # Clear existing exercises and add new ones
                RoutineExercise.objects.filter(routine=routine).delete()
                
                exercise_items = _extract_routine_exercises(request)
                routine_exercise_payload = _build_routine_exercise_payload(
                    user=request.user,
                    exercise_items=exercise_items,
                )
                
                RoutineExercise.objects.bulk_create([
                    RoutineExercise(routine=routine, **item)
                    for item in routine_exercise_payload
                ])

                messages.success(request, "Rutina actualizada correctamente.")
                return redirect("routine-detail", routine_id=routine_id)
            except Exception as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, "Revisa los datos de la rutina para continuar.")

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "exercise_choices": exercise_choices,
                "routine": routine,
                "routine_id": routine_id,
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


class RoutineSelectForDayView(LoginRequiredMixin, View):
    template_name = "routine_select_for_day.html"

    def get(self, request, day_index):
        """Show all user routines to select one for a specific day"""
        routines = get_user_routines(request.user)
        current_schedule = RoutineSchedule.objects.filter(
            user=request.user, day_of_week=day_index
        ).first()
        
        day_labels = dict(RoutineSchedule.DAY_CHOICES)
        day_label = day_labels.get(day_index, "Desconocido")

        return render(
            request,
            self.template_name,
            {
                "routines": routines,
                "day_index": day_index,
                "day_label": day_label,
                "current_routine": current_schedule.routine if current_schedule else None,
            },
        )

    def post(self, request, day_index):
        """Assign selected routine to the specified day"""
        routine_id = request.POST.get("routine_id")
        
        try:
            if routine_id:
                routine = Routine.objects.get(id=routine_id, user=request.user)
                # Delete existing schedule for this day
                RoutineSchedule.objects.filter(
                    user=request.user, day_of_week=day_index
                ).delete()
                # Create new schedule
                RoutineSchedule.objects.create(
                    user=request.user,
                    routine=routine,
                    day_of_week=day_index,
                )
                messages.success(request, f"Rutina '{routine.name}' asignada correctamente.")
            else:
                # Remove routine from day
                RoutineSchedule.objects.filter(
                    user=request.user, day_of_week=day_index
                ).delete()
                messages.success(request, "Rutina removida del día.")
        except Routine.DoesNotExist:
            messages.error(request, "Rutina no encontrada.")
        except Exception as exc:
            messages.error(request, f"Error al asignar rutina: {str(exc)}")

        return redirect("dashboard-home")
 
class MealSelectForDayView(LoginRequiredMixin, View):
    template_name = "meal_select_for_day.html"

    def get(self, request, day_index):
        """Show user's meals to add to a specific day"""
        # Get available meals: user's own plus predefined ones
        user_meals = list(Meal.objects.filter(user=request.user))
        predefined_meals = list(Meal.objects.filter(is_predefined=True))
        meals = user_meals + [m for m in predefined_meals if m not in user_meals]

        # Compute the target date for the selected weekday in the current week
        today = timezone.localdate()
        today_weekday = today.weekday()
        days_ahead = (day_index - today_weekday) % 7
        target_date = today + timezone.timedelta(days=days_ahead)

        # Get existing meal logs for that date
        daily_log = DailyLog.objects.filter(user=request.user, log_date=target_date).first()
        current_meal_logs = []
        if daily_log:
            current_meal_logs = list(daily_log.meals.select_related('meal'))

        day_labels = dict(RoutineSchedule.DAY_CHOICES)
        day_label = day_labels.get(day_index, "Desconocido")

        return render(
            request,
            self.template_name,
            {
                "meals": meals,
                "day_index": day_index,
                "day_label": day_label,
                "target_date": target_date,
                "current_meal_logs": current_meal_logs,
            },
        )

    def post(self, request, day_index):
        meal_type = request.POST.get("meal_type") or "other"

        try:
            # compute target date for the day index
            today = timezone.localdate()
            today_weekday = today.weekday()
            days_ahead = (day_index - today_weekday) % 7
            target_date = today + timezone.timedelta(days=days_ahead)

            # ensure DailyLog exists
            daily_log, _ = DailyLog.objects.get_or_create(user=request.user, log_date=target_date)

            # collect selected meals
            selected = []
            for key in request.POST:
                if not key.startswith("selected_meal_"):
                    continue
                meal_id = key.rsplit("_", 1)[-1]
                selected.append(meal_id)

            if not selected:
                messages.error(request, "No seleccionaste ninguna comida.")
                return redirect("meal-select-for-day", day_index=day_index)

            for meal_id in selected:
                meal = Meal.objects.filter(id=meal_id).first()
                if not meal:
                    continue
                qty = request.POST.get(f"quantity_{meal_id}") or 1.0
                eaten_at = timezone.now()
                MealLog.objects.create(
                    user=request.user,
                    meal=meal,
                    daily_log=daily_log,
                    eaten_at=eaten_at,
                    quantity=float(qty),
                    meal_type=meal_type,
                )

            messages.success(request, f"{len(selected)} comida(s) agregada(s) para {target_date}.")
        except Exception as exc:
            messages.error(request, f"Error al agregar comida: {str(exc)}")

        # After successfully adding meals for the day, return to the dashboard home
        return redirect("dashboard-home")


class MealLogDeleteView(LoginRequiredMixin, View):
    def post(self, request, meal_log_id):
        try:
            log = MealLog.objects.select_related('daily_log').filter(id=meal_log_id, user=request.user).first()
            if not log:
                messages.error(request, "Registro de comida no encontrado.")
                return redirect('dashboard-home')

            # capture day_index if supplied so we can return to selection page
            day_index = request.POST.get('day_index')
            log.delete()
            messages.success(request, "Registro de comida eliminado.")
            if day_index is not None:
                try:
                    return redirect('meal-select-for-day', day_index=int(day_index))
                except Exception:
                    pass
        except Exception as exc:
            messages.error(request, f"Error al eliminar: {str(exc)}")
        return redirect('dashboard-home')


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
        search_query = request.GET.get("q", "").strip()
        selected_routine_id = request.GET.get("routine")
        selected_meal_plan_id = request.GET.get("meal")
        selected_exercise_id = request.GET.get("exercise")

        routines_qs = Routine.objects.filter(is_public=True).select_related("user").prefetch_related("exercises__exercise").order_by("-created_at")
        meal_plans_qs = MealPlan.objects.filter(is_public=True).select_related("user").prefetch_related("items__meal").order_by("-created_at")
        meals_qs = Meal.objects.filter(Q(is_predefined=True) | Q(user__isnull=False)).select_related("user", "category").order_by("-id")
        exercises_qs = Exercise.objects.exclude(user__isnull=True).select_related("user").order_by("-id")

        if request.user.is_authenticated:
            routines_qs = routines_qs.exclude(user=request.user)
            meal_plans_qs = meal_plans_qs.exclude(user=request.user)
            meals_qs = meals_qs.exclude(user=request.user)
            exercises_qs = exercises_qs.exclude(user=request.user)

        public_routines = list(routines_qs[:20])
        search_mode = "none"
        search_provider = "none"

        if tab == "meals" and search_query:
            ranked_meals, search_mode, search_provider = _semantic_rank_by_title(list(meal_plans_qs[:100]), search_query, "name")
            public_meal_plans = ranked_meals[:20]
            ranked_public_meals, meal_search_mode, meal_search_provider = _semantic_rank_by_title(list(meals_qs[:100]), search_query, "name")
            public_meals = ranked_public_meals[:20]
        else:
            public_meal_plans = list(meal_plans_qs[:20])
            public_meals = list(meals_qs[:20])

        if tab == "exercises" and search_query:
            ranked_exercises, search_mode, search_provider = _semantic_rank_by_title(list(exercises_qs[:100]), search_query, "name")
            public_exercises = ranked_exercises[:20]
        else:
            public_exercises = list(exercises_qs[:20])

        saved_routine_ids = set()
        saved_meal_ids = set()
        saved_meal_plan_ids = set()
        saved_exercise_ids = set()
        if request.user.is_authenticated:
            saved_routine_ids = set(
                Routine.objects.filter(user=request.user, source_routine__isnull=False)
                .values_list("source_routine_id", flat=True)
            )
            saved_meal_ids = set(
                FavoriteMeal.objects.filter(user=request.user)
                .values_list("meal_id", flat=True)
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
                "public_meals": public_meals,
                "public_exercises": public_exercises,
                "is_authenticated": request.user.is_authenticated,
                "active_tab": tab if tab in {"routines", "meals", "exercises"} else "routines",
                "search_query": search_query,
                "embedding_search_enabled": _has_embedding_provider_configured(),
                "search_mode": search_mode,
                "search_provider": search_provider,
                "selected_routine": selected_routine,
                "selected_meal_plan": selected_meal_plan,
                "selected_exercise": selected_exercise,
                "routine_already_saved": routine_already_saved,
                "meal_plan_already_saved": meal_plan_already_saved,
                "exercise_already_saved": exercise_already_saved,
                "saved_routine_ids": saved_routine_ids,
                "saved_meal_ids": saved_meal_ids,
                "saved_meal_plan_ids": saved_meal_plan_ids,
                "saved_exercise_ids": saved_exercise_ids,
            },
        )

    def post(self, request):
        routine_id = request.POST.get("routine_id")
        meal_id = request.POST.get("meal_id")
        meal_plan_id = request.POST.get("meal_plan_id")
        exercise_id = request.POST.get("exercise_id")

        if meal_id:
            if not request.user.is_authenticated:
                messages.error(request, "Debes iniciar sesion para guardar una comida.")
                return redirect(f"/login/?next=/social/?tab=meals&meal={meal_id}")

            source_meal = Meal.objects.filter(id=meal_id).select_related("user", "category").first()
            if not source_meal:
                messages.error(request, "La comida no existe o ya no esta disponible.")
                return redirect("/social/?tab=meals")

            if source_meal.user_id == request.user.id:
                messages.info(request, "Esta comida ya es tuya.")
                return redirect(f"/social/?tab=meals&meal={source_meal.id}")

            favorite_meal, created = FavoriteMeal.objects.get_or_create(
                user=request.user,
                meal=source_meal,
            )
            if created:
                messages.success(request, "Comida guardada en tu perfil.")
            else:
                messages.info(request, "Esta comida ya esta guardada en tu perfil.")
            return redirect(f"/social/?tab=meals&meal={source_meal.id}")

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


class DietView(LoginRequiredMixin, View):
    template_name = "diet.html"

    def get(self, request):
        # Show meals that are either predefined or belong to the current user
        user_or_predef = Q(is_predefined=True) | Q(user=request.user)
        breakfast = Meal.objects.filter(category__name="Desayuno").filter(user_or_predef)
        lunch = Meal.objects.filter(category__name="Almuerzo").filter(user_or_predef)
        dinner = Meal.objects.filter(category__name="Cena").filter(user_or_predef)

        favorite_relations = FavoriteMeal.objects.filter(user=request.user)
        favorite_meals = [fav.meal for fav in favorite_relations]
        favorite_ids = {meal.id for meal in favorite_meals}

        form = MealForm()

        return render(request, self.template_name, {
            "breakfast": breakfast,
            "lunch": lunch,
            "dinner": dinner,
            "favorite_meals": favorite_meals,
            "favorite_ids": favorite_ids,
            "form": form
        })


@login_required
def add_meal(request):
    if request.method == 'POST':
        form = MealForm(request.POST, request.FILES)
        if form.is_valid():
            meal = form.save(commit=False)
            meal.user = request.user

            meal.save()
    return redirect('diet')