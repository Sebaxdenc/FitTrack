"""
Comando de Django para asignar imágenes ya generadas desde la carpeta
media/meals/ a cada comida en la base de datos.

Uso:
    python manage.py update_meal_images_from_folder

    No requiere API key — solo trabaja con archivos locales.
    Equivalente a `update_images_from_folder` del ejemplo de películas.

Convención de nombres de archivo:
    m_NombreComida.png   →   Comida con name="NombreComida"
    (espacios en el nombre se reemplazan por _ en el archivo)
"""

import os

from django.core.management.base import BaseCommand

from workouts.models import Meal


class Command(BaseCommand):
    help = (
        "Asigna imágenes preexistentes de media/meals/ a las comidas en la base de datos"
    )

    def handle(self, *args, **kwargs):
        images_folder = "media/meals/"

        if not os.path.isdir(images_folder):
            self.stderr.write(
                self.style.ERROR(
                    f" La carpeta '{images_folder}' no existe. "
                    "Copia las imágenes allí primero."
                )
            )
            return

        # Índice de archivos disponibles para búsqueda rápida
        available_files = {f.lower(): f for f in os.listdir(images_folder)}

        meals = Meal.objects.all()
        self.stdout.write(f" Se encontraron {meals.count()} comidas en la base de datos.")

        updated = 0
        skipped = 0
        not_found = 0

        for meal in meals:
            # Construir nombre de archivo esperado
            safe_name = meal.name.replace(" ", "_").replace("/", "-")
            expected_filename = f"m_{safe_name}.png"

            # Búsqueda case-insensitive
            matched_filename = available_files.get(expected_filename.lower())

            if matched_filename:
                relative_path = os.path.join("meals", matched_filename)
                meal.image = relative_path
                meal.save()
                self.stdout.write(
                    self.style.SUCCESS(f" '{meal.name}' → {matched_filename}")
                )
                updated += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"  No se encontró imagen para: '{meal.name}' "
                        f"(buscaba: {expected_filename})"
                    )
                )
                not_found += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🏁 Finalizado: {updated} actualizadas, "
                f"{skipped} saltadas, {not_found} sin imagen."
            )
        )