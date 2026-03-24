import shutil
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

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
                "type": "Fuerza",
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
        self.assertTrue(exercise.equipment_photo.name.startswith("exercise-equipment/"))
        self.assertEqual(exercise.image_url, "")
        self.assertTrue(exercise.display_image_url.startswith("/media/exercise-equipment/"))


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
