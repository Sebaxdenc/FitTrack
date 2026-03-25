from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
import random
from datetime import timedelta
from django.utils import timezone

from workouts.models import *

User = get_user_model()


class Command(BaseCommand):
    help = "Seed FITtrack fake data"

    def handle(self, *args, **kwargs):

        fake = Faker()

        self.stdout.write("Creating user...")

        user, _ = User.objects.get_or_create(
            username="demo",
            defaults={
                "email": "demo@test.com"
            }
        )
        user.set_password("1234")
        user.save()

        Profile.objects.get_or_create(
            user=user,
            bio=fake.text()
        )

        # ---------------- MEALS ----------------

        meals = []

        for _ in range(25):
            meal = Meal.objects.create(
                name=fake.word().title(),
                calories=random.randint(200, 800),
                carbs_g=random.randint(10, 80),
                protein_g=random.randint(10, 60),
                fat_g=random.randint(5, 30),
                is_predefined=True
            )
            meals.append(meal)

        # favorites + ratings
        for meal in random.sample(meals, 10):
            FavoriteMeal.objects.create(user=user, meal=meal)

            MealRating.objects.create(
                user=user,
                meal=meal,
                score=random.randint(3, 5),
                comment=fake.sentence()
            )

        # ---------------- EXERCISES ----------------

        exercises = []

        for _ in range(20):
            ex = Exercise.objects.create(
                user=user,
                name=fake.word().title(),
                muscle_group=random.choice(
                    ["Chest", "Back", "Legs", "Arms", "Shoulders"]
                ),
                type=random.choice(["Strength", "Cardio"]),
                image_url="https://picsum.photos/200"
            )
            exercises.append(ex)

        for ex in random.sample(exercises, 8):
            FavoriteExercise.objects.create(user=user, exercise=ex)

            ExerciseRating.objects.create(
                user=user,
                exercise=ex,
                score=random.randint(3, 5),
                comment=fake.sentence()
            )

        # ---------------- ROUTINES ----------------

        routines = []

        for _ in range(4):
            routine = Routine.objects.create(
                user=user,
                name=f"{fake.word().title()} Routine",
                goal=random.choice(["Strength", "Hypertrophy", "Fat Loss"]),
            )
            routines.append(routine)

            order = 1
            for ex in random.sample(exercises, 5):
                RoutineExercise.objects.create(
                    routine=routine,
                    exercise=ex,
                    sort_order=order,
                    target_sets=random.randint(3, 5),
                    target_reps=random.randint(8, 12),
                    rest_seconds=random.randint(60, 120),
                )
                order += 1

        # schedule weekly
        for day in range(7):
            RoutineSchedule.objects.create(
                user=user,
                routine=random.choice(routines),
                day_of_week=day
            )

        # ---------------- WORKOUTS ----------------

        workouts = []

        for i in range(40):

            started = timezone.now() - timedelta(days=random.randint(0, 30))

            workout = Workout.objects.create(
                user=user,
                routine=random.choice(routines),
                started_at=started,
                duration_minutes=random.randint(30, 90),
                notes=fake.sentence()
            )
            workouts.append(workout)

            for set_n in range(1, random.randint(4, 7)):
                WorkoutSet.objects.create(
                    workout=workout,
                    exercise=random.choice(exercises),
                    set_number=set_n,
                    reps=random.randint(6, 12),
                    weight=random.randint(20, 100),
                    rest_seconds=random.randint(60, 120),
                    is_warmup=random.choice([True, False])
                )

        # ---------------- DAILY GOALS + LOGS ----------------

        for i in range(30):
            day = timezone.now().date() - timedelta(days=i)

            target = random.randint(300, 600)
            current = random.randint(0, 700)

            DailyGoal.objects.create(
                user=user,
                goal_date=day,
                burn_calories_target=target,
                burn_calories_current=current,
                completed=current >= target
            )

            log = DailyLog.objects.create(
                user=user,
                log_date=day,
                total_calories_consumed=random.randint(1800, 2800),
                total_calories_burned=random.randint(200, 700)
            )

            for _ in range(random.randint(2, 4)):
                MealLog.objects.create(
                    user=user,
                    meal=random.choice(meals),
                    daily_log=log,
                    eaten_at=timezone.now() - timedelta(days=i),
                    quantity=random.uniform(0.5, 2),
                    meal_type=random.choice(["Breakfast", "Lunch", "Dinner"])
                )

        # ---------------- ACHIEVEMENTS ----------------

        for _ in range(10):
            Achievement.objects.create(
                user=user,
                title=fake.word().title(),
                description=fake.sentence()
            )

        # ---------------- EQUIPMENT ----------------

        for _ in range(6):
            EquipmentRecommendation.objects.create(
                name=fake.word().title(),
                category=random.choice(["Weights", "Cardio", "Accessory"]),
                description=fake.text(),
                link="https://amazon.com"
            )

        # ============ SOCIAL FEED DATA ============
        
        self.stdout.write("Creating social feed data...")

        # Create demo social users
        social_users = []
        for i in range(3):
            social_user, _ = User.objects.get_or_create(
                username=f"athlete_{i+1}",
                defaults={"email": f"athlete{i+1}@fittrack.com"}
            )
            social_user.set_password("1234")
            social_user.save()
            
            Profile.objects.get_or_create(
                user=social_user,
                defaults={"bio": fake.text()}
            )
            social_users.append(social_user)

        # Create social exercises
        social_exercises = []
        for _ in range(10):
            ex = Exercise.objects.create(
                user=random.choice(social_users),
                name=fake.word().title(),
                muscle_group=random.choice(
                    ["Pecho", "Espalda", "Piernas", "Brazos", "Hombros"]
                ),
                type=random.choice(["Fuerza", "Cardio"]),
                image_url="https://picsum.photos/200"
            )
            social_exercises.append(ex)

        # Create public routines
        for _ in range(6):
            social_user = random.choice(social_users)
            routine = Routine.objects.create(
                user=social_user,
                name=f"Rutina {fake.word().title()}",
                goal=random.choice(["Fuerza", "Hipertrofia", "Pérdida de Grasa", "Resistencia"]),
                description=fake.sentence(),
                is_public=True
            )

            order = 1
            for ex in random.sample(social_exercises, min(4, len(social_exercises))):
                RoutineExercise.objects.create(
                    routine=routine,
                    exercise=ex,
                    sort_order=order,
                    target_sets=random.randint(3, 5),
                    target_reps=random.randint(8, 12),
                    rest_seconds=random.randint(60, 120),
                )
                order += 1

        # Create public meal plans
        for _ in range(4):
            social_user = random.choice(social_users)
            meal_plan = MealPlan.objects.create(
                user=social_user,
                name=f"Plan {fake.word().title()}",
                description=fake.sentence(),
                is_public=True
            )

            order = 1
            for meal in random.sample(meals, min(5, len(meals))):
                MealItem.objects.create(
                    meal_plan=meal_plan,
                    meal=meal,
                    quantity=random.uniform(0.5, 2),
                    meal_type=random.choice(["Desayuno", "Almuerzo", "Cena", "Snack"]),
                    sort_order=order
                )
                order += 1

        self.stdout.write(self.style.SUCCESS("🔥 FITtrack Seed COMPLETED"))