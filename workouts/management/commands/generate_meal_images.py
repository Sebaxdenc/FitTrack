"""
Comando de Django para generar imágenes de comidas usando la API de Hugging Face.

Uso:
    python manage.py generate_meal_images

    Solo procesa la PRIMERA comida sin imagen para ahorrar cuota de API.
    Quita el `break` para procesar todas las comidas.

Requiere:
    - pip install requests python-dotenv
    - Variable HUGGINGFACE_API_TOKEN o HF_TOKEN en .env (raíz del proyecto)
"""

import os
import requests

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from dotenv import load_dotenv

from workouts.models import Meal


class Command(BaseCommand):
    help = "Genera imágenes para las comidas usando la API de Hugging Face"

    def handle(self, *args, **kwargs):
        load_dotenv(".env")
        load_dotenv("../.env")

        hf_token = os.environ.get("HUGGINGFACE_API_TOKEN") or os.environ.get("HF_TOKEN")
        if not hf_token:
            self.stderr.write(self.style.ERROR(
                "No se encontro HUGGINGFACE_API_TOKEN ni HF_TOKEN. "
                "Agrega una de esas variables en tu .env"
            ))
            return

        meals = Meal.objects.all()
        self.stdout.write(f"Se encontraron {meals.count()} comidas en la base de datos.")

        for meal in meals:
            if meal.image:
                self.stdout.write(f"'{meal.name}' ya tiene imagen. Saltando...")
                continue

            self.stdout.write(f"Generando imagen para: {meal.name}")

            try:
                image_relative_path = self.generate_and_download_image(
                    hf_token, meal.name
                )
                meal.image = image_relative_path
                meal.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Imagen guardada y actualizada para: {meal.name}")
                )
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"Error generando imagen para '{meal.name}': {e}")
                )




        self.stdout.write(self.style.SUCCESS("Proceso finalizado."))

    def generate_and_download_image(self, hf_token: str, meal_name: str) -> str:
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

        response = requests.post(url, headers=headers, json=payload, timeout=120)
        if response.status_code >= 400:
            raise ValueError(f"Hugging Face devolvio {response.status_code}: {response.text[:300]}")

        content_type = response.headers.get("Content-Type", "")
        if "image" not in content_type.lower():
            raise ValueError(f"Hugging Face no devolvio una imagen valida: {response.text[:300]}")

        safe_name = meal_name.replace(" ", "_").replace("/", "-")
        image_filename = f"m_{safe_name}.png"
        image_path = os.path.join("meals", image_filename)

        saved_path = default_storage.save(image_path, ContentFile(response.content))

        return saved_path