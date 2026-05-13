from django.core.management.base import BaseCommand
from workouts.models import MealCategory


class Command(BaseCommand):
    help = 'Create default meal categories'

    def handle(self, *args, **options):
        categories = ['Desayuno', 'Almuerzo', 'Cena']
        
        for category_name in categories:
            category, created = MealCategory.objects.get_or_create(name=category_name)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Categoría creada: {category_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'→ Categoría ya existe: {category_name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('\n✓ Todas las categorías están listas.')
        )
