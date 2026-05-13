from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

from .models import Exercise, Profile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=get_user_model())
def create_user_defaults(sender, instance, created, **kwargs):
    """When a new user is created, seed a small set of default exercises and a Profile.

    This avoids empty dashboards and gives users quick starters.
    If the user already has created_exercises we don't duplicate them.
    """
    if not created:
        return

    try:
        # Ensure profile exists
        Profile.objects.get_or_create(user=instance)

        # If user already has exercises, skip
        if Exercise.objects.filter(user=instance).exists():
            return

        defaults = [
            {"name": "Sentadillas", "muscle_group": "Piernas", "description": "Sentadillas básicas para fuerza de piernas.", "image_url": "https://picsum.photos/200?1"},
            {"name": "Flexiones", "muscle_group": "Pecho", "description": "Flexiones de pecho estándar.", "image_url": "https://picsum.photos/200?2"},
            {"name": "Plancha", "muscle_group": "Core", "description": "Plancha isométrica para core.", "image_url": "https://picsum.photos/200?3"},
            {"name": "Remo con mancuerna", "muscle_group": "Espalda", "description": "Remo con mancuerna para espalda.", "image_url": "https://picsum.photos/200?4"},
            {"name": "Elevaciones laterales", "muscle_group": "Hombros", "description": "Elevaciones laterales para deltoides.", "image_url": "https://picsum.photos/200?5"},
        ]

        created = 0
        for data in defaults:
            try:
                Exercise.objects.create(user=instance, **data)
                created += 1
            except Exception as exc:
                # Log but continue creating the rest
                logger.exception("Failed creating default exercise %s for user %s: %s", data.get('name'), instance, exc)

        logger.info("Created %d default exercises for user %s", created, instance)
    except Exception as exc:
        logger.exception("Failed to create default exercises for new user %s: %s", instance, exc)


@receiver(post_save, sender=Exercise)
def generate_exercise_image_on_create(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.equipment_photo or instance.image_url:
        return

    try:
        from .exercise_image_generation import generate_exercise_image

        image_path = generate_exercise_image(instance.name, instance.muscle_group)
        if image_path:
            Exercise.objects.filter(pk=instance.pk).update(equipment_photo=image_path)
    except Exception as exc:
        logger.exception("Failed to generate exercise image for %s: %s", instance, exc)
