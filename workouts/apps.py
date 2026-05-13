from django.apps import AppConfig


class WorkoutsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'workouts'
    
    def ready(self):
        # Import signals to ensure they are registered when the app is ready
        try:
            import workouts.signals  # noqa: F401
        except Exception:
            # Avoid raising on import errors during migrations or installs; log instead
            import logging
            logging.getLogger(__name__).exception("Failed to import workouts.signals")
