"""
Comando de Django para generar imágenes de comidas usando la API de Google Gemini.

Uso:
    python manage.py generate_meal_images

    Solo procesa la PRIMERA comida sin imagen para ahorrar cuota de API.
    Quita el `break` para procesar todas las comidas.

Requiere:
    - pip install requests python-dotenv
    - Variable GEMINI_API_KEY en gemini.env (raíz del proyecto)
"""

import os
import base64
import requests

from django.core.management.base import BaseCommand
from dotenv import load_dotenv

from workouts.models import Meal


class Command(BaseCommand):
    help = "Genera imágenes para las comidas usando la API de Google Gemini"

    def handle(self, *args, **kwargs):
        # Cargar clave de API
        load_dotenv("gemini.env")
        load_dotenv("../gemini.env")

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            self.stderr.write(self.style.ERROR(
                "No se encontro GEMINI_API_KEY. "
                "Crea el archivo gemini.env con: GEMINI_API_KEY=tu_clave"
            ))
            return

        images_folder = "media/meals/"
        os.makedirs(images_folder, exist_ok=True)

        meals = Meal.objects.all()
        self.stdout.write(f"Se encontraron {meals.count()} comidas en la base de datos.")

        for meal in meals:
            if meal.image:
                self.stdout.write(f"'{meal.name}' ya tiene imagen. Saltando...")
                continue

            self.stdout.write(f"Generando imagen para: {meal.name}")

            try:
                image_relative_path = self.generate_and_download_image(
                    api_key, meal.name, images_folder
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

    def generate_and_download_image(self, api_key: str, meal_name: str, save_folder: str) -> str:
        prompt = (
            f"High quality food photography of '{meal_name}', "
            "served on a clean white plate, professional studio lighting, "
            "top-down view, appetizing, vibrant colors, no text."
        )

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash-image:generateContent?key={api_key}"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
        }

        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        parts = data["candidates"][0]["content"]["parts"]
        image_b64 = None
        for part in parts:
            if "inlineData" in part:
                image_b64 = part["inlineData"]["data"]
    

        if not image_b64:
            raise ValueError("La API no devolvio ninguna imagen en la respuesta.")

        image_bytes = base64.b64decode(image_b64)

        safe_name = meal_name.replace(" ", "_").replace("/", "-")
        image_filename = f"m_{safe_name}.png"
        image_path_full = os.path.join(save_folder, image_filename)

        with open(image_path_full, "wb") as f:
            f.write(image_bytes)

        return os.path.join("meals", image_filename)