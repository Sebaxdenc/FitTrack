import logging
import os
import time

import requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def generate_meal_image(meal_name: str):
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
    image_filename = f"m_{safe_name}.png"
    image_path = os.path.join("meals", image_filename)

    last_error = None
    for attempt in range(3):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)

            if response.status_code == 503:
                time.sleep(2 ** attempt)
                continue

            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "image" not in content_type.lower():
                error_data = response.json() if response.content else {}
                raise ValueError(f"Hugging Face no devolvio una imagen valida: {error_data}")

            saved_path = default_storage.save(image_path, ContentFile(response.content))
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