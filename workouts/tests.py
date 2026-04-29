import shutil
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .exceptions import (
    ExerciseDescriptionConfigurationError,
    ExerciseDescriptionGenerationError,
)
from .models import Exercise

User = get_user_model()
TEST_MEDIA_ROOT = Path(__file__).resolve().parent.parent / "test_media"
TEST_GIF_BYTES = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
    b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00"
    b"\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT, MEDIA_URL="/media/")
class ExerciseCreationTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="secret123")
        self.client.force_login(self.user)

    def test_user_can_create_exercise_with_uploaded_equipment_photo(self):
        response = self.client.post(
            reverse("routine-exercise-list"),
            {
                "name": "Press militar",
                "muscle_group": "Hombros",
                "description": "Ejercicio de empuje para fortalecer hombros y triceps.",
                "image_url": "",
                "equipment_photo": SimpleUploadedFile(
                    "mancuerna.gif",
                    TEST_GIF_BYTES,
                    content_type="image/gif",
                ),
            },
        )

        self.assertRedirects(response, reverse("routine-exercise-list"))
        exercise = Exercise.objects.get(name="Press militar")
        self.assertEqual(exercise.description, "Ejercicio de empuje para fortalecer hombros y triceps.")
        self.assertTrue(exercise.equipment_photo.name.startswith("exercise-equipment/"))
        self.assertEqual(exercise.image_url, "")
        self.assertTrue(exercise.display_image_url.startswith("/media/exercise-equipment/"))

    @patch("workouts.frontend_views.generate_exercise_description")
    def test_generate_description_endpoint_returns_ai_text(self, generate_description_mock):
        generate_description_mock.return_value = (
            "Ejercicio de empuje que fortalece los hombros y mejora la estabilidad superior. "
            "Ideal para trabajar control y fuerza con una tecnica consistente."
        )

        response = self.client.post(
            reverse("exercise-description-generate"),
            data='{"name":"Press militar","muscle_group":"Hombros","description":""}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                "description": (
                    "Ejercicio de empuje que fortalece los hombros y mejora la estabilidad superior. "
                    "Ideal para trabajar control y fuerza con una tecnica consistente."
                )
            },
        )
        generate_description_mock.assert_called_once_with(
            name="Press militar",
            muscle_group="Hombros",
            current_description="",
        )

    @patch("workouts.frontend_views.generate_exercise_description")
    def test_generate_description_endpoint_uses_existing_draft(self, generate_description_mock):
        generate_description_mock.return_value = "Descripcion reescrita."

        response = self.client.post(
            reverse("exercise-description-generate"),
            data=(
                '{"name":"Sentadilla","muscle_group":"Piernas",'
                '"description":"trabaja piernas pero quiero mejorar este texto"}'
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"description": "Descripcion reescrita."})
        generate_description_mock.assert_called_once_with(
            name="Sentadilla",
            muscle_group="Piernas",
            current_description="trabaja piernas pero quiero mejorar este texto",
        )

    def test_generate_description_endpoint_requires_name_and_muscle_group(self):
        response = self.client.post(
            reverse("exercise-description-generate"),
            data='{"name":"","muscle_group":"","description":"algo"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {"error": "Debes completar nombre y grupo muscular antes de usar la IA."},
        )

    @patch("workouts.frontend_views.generate_exercise_description")
    def test_generate_description_endpoint_returns_configuration_error(self, generate_description_mock):
        generate_description_mock.side_effect = ExerciseDescriptionConfigurationError(
            "La generacion con IA no esta configurada en este entorno."
        )

        response = self.client.post(
            reverse("exercise-description-generate"),
            data='{"name":"Plancha","muscle_group":"Core","description":""}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertJSONEqual(
            response.content,
            {"error": "La generacion con IA no esta configurada en este entorno."},
        )

    @patch("workouts.frontend_views.generate_exercise_description")
    def test_generate_description_endpoint_returns_provider_error(self, generate_description_mock):
        generate_description_mock.side_effect = ExerciseDescriptionGenerationError(
            "No pudimos generar la descripcion en este momento."
        )

        response = self.client.post(
            reverse("exercise-description-generate"),
            data='{"name":"Burpee","muscle_group":"Cuerpo completo","description":"borrador"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 502)
        self.assertJSONEqual(
            response.content,
            {"error": "No pudimos generar la descripcion en este momento."},
        )


class RoutineViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="routine_tester", password="secret123")
        self.client.force_login(self.user)

    def test_logged_user_can_open_routine_list_view(self):
        response = self.client.get(reverse("routine-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tus rutinas")
        self.assertContains(response, "Crear rutina")

    def test_routine_frontend_and_api_have_different_route_names(self):
        self.assertEqual(reverse("routine-list"), "/rutinas/")
        self.assertEqual(reverse("api:routine-list"), "/api/routines/")

    def test_english_alias_for_routine_list_opens_frontend_view(self):
        response = self.client.get("/routines/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tus rutinas")
